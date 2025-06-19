import aiohttp
import asyncio
import pandas as pd
import nest_asyncio
import numpy as np
from datetime import date

# Allow nested asyncio calls in environments with a running event loop
nest_asyncio.apply()

async def get_player_gameweek_data(player_id, session):
    """Fetch gameweek data and upcoming fixtures for a specific player."""
    url = f"https://fantasy.premierleague.com/api/element-summary/{player_id}/"
    async with session.get(url) as response:
        data = await response.json()
        gameweek_data = data['history']  # Gameweek data for this player
        fixtures = data['fixtures']  # Upcoming fixtures for this player
        return gameweek_data, fixtures

async def get_all_players():
    url = "https://fantasy.premierleague.com/api/bootstrap-static/"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()
            players = data['elements']  # List of all players
            teams = data['teams']  # List of teams

            # Create a mapping from team ID to team name
            team_mapping = {team['id']: team['name'] for team in teams}

            # Extract a comprehensive set of fields for each player
            players_data = []
            for player in players:
                # Fetch gameweek data and fixtures for this player
                gameweek_data, fixtures = await get_player_gameweek_data(player['id'], session)

                # Calculate average fixture difficulty for upcoming matches
                upcoming_fixtures = [f for f in fixtures if not f['finished']]
                if upcoming_fixtures:
                    avg_difficulty = np.mean([f['difficulty'] for f in upcoming_fixtures])
                else:
                    avg_difficulty = np.nan  # No upcoming fixtures

                player_info = {
                    "Player ID": player['id'],
                    "Player Name": player['web_name'],
                    "Full Name": f"{player['first_name']} {player['second_name']}",
                    "Team ID": player['team'],
                    "Team Name": team_mapping[player['team']],
                    "Position": player['element_type'],
                    "Cost (£)": player['now_cost'] / 10,
                    "Total Points": player['total_points'],
                    "ICT Index": player['ict_index'],
                    "Threat": player['threat'],  # Most recent threat score
                    "Points Per Game": player['points_per_game'],
                    "Expected Points (This GW)": player['ep_this'],
                    "Expected Points (Next GW)": player['ep_next'],
                    "Current Form": player['form'],
                    "Status": player['status'],
                    "Chance of Playing Next GW (%)": player.get('chance_of_playing_next_round', "N/A"),
                    "News": player['news'],
                    "Avg Fixture Difficulty (Upcoming)": avg_difficulty
                }

                # Append each gameweek's data as a row, adding player details
                for gw in gameweek_data:
                    gameweek_info = {
                        **player_info,
                        "Game Week": gw['round'],
                        "Goals Scored": gw['goals_scored'],
                        "Assists": gw['assists'],
                        "Clean Sheets": gw['clean_sheets'],
                        "Minutes Played": gw['minutes'],
                        "Bonus Points": gw['bonus'],
                        "Yellow Cards": gw['yellow_cards'],
                        "Red Cards": gw['red_cards'],
                        "Points": gw['total_points'],
                        "Transfers In": gw['transfers_in'],
                        "Transfers Out": gw['transfers_out']
                    }
                    players_data.append(gameweek_info)

            # Create a DataFrame with player stats by gameweek
            df = pd.DataFrame(players_data)

            #df = df.sort_values('Game Week', ascending=False).drop_duplicates('Player ID')

            # Calculate exponential weights for each gameweek
            alpha = 0.1  # Growth rate for weights
            df['Weight'] = np.exp(alpha * (df['Game Week'] - 1))
            df['Weighted Points'] = df['Points'] * df['Weight']

            # Calculate total points for the last 4 gameweeks
            recent_weeks = sorted(df['Game Week'].unique(), reverse=True)[:4]
            df['Recent 4 Weeks Points'] = df.apply(
                lambda row: row['Points'] if row['Game Week'] in recent_weeks else 0, axis=1
            )

            recent_third = sorted(df['Game Week'].unique(), reverse=True)[:8]
            df['Recent 8 Weeks Points'] = df.apply(
                lambda row: row['Points'] if row['Game Week'] in recent_third else 0, axis=1
            )

            # Calculate over and under 3 points stats
            df['Over 3 Points'] = df['Points'] > 3
            df['3 Points and Under'] = df['Points'] <= 3

            # Summarize by player, including cost and team name
            player_summary_all = df.groupby(
                'Player ID'
            ).agg({
                'Points': 'sum',
                'Weighted Points': 'sum',
                'Goals Scored': 'sum',
                'Assists': 'sum',
                'Clean Sheets': 'sum',
                'Minutes Played': 'sum',
                'Recent 4 Weeks Points': 'sum',
                'Recent 8 Weeks Points': 'sum'

            }).reset_index()

            df_current = df.drop(columns=['Points', 'Weighted Points', 'Goals Scored',
       'Assists', 'Clean Sheets', 'Minutes Played',
       'Recent 4 Weeks Points','Recent 8 Weeks Points']).sort_values('Game Week', ascending=False).drop_duplicates('Player ID')
            # Merge the most recent metrics with the aggregated data
            final_summary = pd.merge(
                player_summary_all,
                df_current,
                on=['Player ID'],
                how='left'
                )

            ratio_df = df.groupby(['Player ID']).agg({
                'Points': 'count',
                'Over 3 Points': 'sum',
                '3 Points and Under': 'sum'
            }).rename(columns={'Points': 'Games Played'}).reset_index()

            # Calculate the ratio
            ratio_df['Ratio'] = (ratio_df['Over 3 Points'] / ratio_df['3 Points and Under']) * ratio_df['Games Played']

            #exclude 3 Points and Under,Over 3 Points, from df table
            merge_df = final_summary.drop(columns=['Over 3 Points', '3 Points and Under'])

            # Merge the summarized data with the ratio analysis
            player_summary_combined = merge_df.merge(
                ratio_df,
                on='Player ID', how='left'
            )
            #reorder player_summary_combined columns with all available columns

            player_summary_combined = player_summary_combined[
                ['Player Name', 'Team Name', 'Position', 'Cost (£)', 'Total Points','Weighted Points','Recent 4 Weeks Points','Recent 8 Weeks Points',
                'Expected Points (This GW)','Expected Points (Next GW)',
                'ICT Index', 'Threat', 'Points Per Game', 'Current Form', 'Status',
                'Chance of Playing Next GW (%)', 'News', 'Avg Fixture Difficulty (Upcoming)',
                'Game Week', 'Goals Scored', 'Assists', 'Clean Sheets', 'Minutes Played',
                'Bonus Points', 'Yellow Cards', 'Red Cards', 'Transfers In',
                'Transfers Out',
                'Games Played', 'Over 3 Points', '3 Points and Under', 'Ratio']
                ]


            return player_summary_combined

# Run the function and save the summarized table to an Excel file
summarized_df = asyncio.run(get_all_players())
summarized_df.sort_values('Weighted Points',ascending=False).to_excel(f"data/Summarized_Player_Performance_{date.today()}.xlsx", index=False)
