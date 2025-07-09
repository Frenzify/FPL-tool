# Fantasy Premier League Player Performance Summary

## Overview

This script fetches and processes Fantasy Premier League (FPL) data to generate a comprehensive summary of player performance by gameweek. It retrieves player statistics, upcoming fixture information, and various performance metrics, then compiles them into a structured Excel report.

The following Looker Studio dashboard is displays the FPL 24-25 season in a user friendly way: https://lookerstudio.google.com/reporting/6790c7f9-d0c1-48e2-95d9-843d88d41541

## Features

* Asynchronously fetches player details, gameweek history, and fixture data from the official FPL API.
* Calculates average fixture difficulty for upcoming matches.
* Computes exponential weightings for recent gameweek points.
* Aggregates key statistics such as total points, goals, assists, clean sheets, and minutes played.
* Calculates performance over the last 4 and 8 gameweeks.
* Determines ratios of high-scoring (>3 points) to low-scoring (≤3 points) appearances.
* Outputs a sorted Excel file (`.xlsx`) with detailed player summaries.

## Prerequisites

* Python 3.8 or higher
* FPL API access (public endpoints)

## Dependencies

Install required packages using pip:

```bash
pip install aiohttp pandas numpy nest_asyncio openpyxl
```

## Usage

1. **Clone the repository** or download the script file.
2. **Install dependencies** as described above.
3. **Run the script**:

   ```bash
   python your_script_name.py
   ```
4. **Output**:

   * The script saves an Excel file named `Summarized_Player_Performance_YYYY-MM-DD.xlsx` in the `data/` directory, containing the final player performance summary.

## Script Structure

* **get\_player\_gameweek\_data(player\_id, session)**

  * Fetches historical gameweek data and upcoming fixtures for a given player.
* **get\_all\_players()**

  * Retrieves all players and team metadata.
  * Iterates through each player to collect gameweek stats and compute metrics.
  * Aggregates and merges per-gameweek and summary data into a final `pandas.DataFrame`.
* **Main Execution**

  * Invokes `asyncio.run(get_all_players())` to obtain the summary DataFrame.
  * Sorts by weighted points and writes the results to an Excel file.

## Configuration

* **Alpha (weight growth rate)** can be adjusted by modifying the `alpha` variable.
* **Recent weeks window** (4 and 8 weeks) is defined in the DataFrame calculations and can be customized.
* **Output directory**: ensure the `data/` folder exists or update the path in the script.

## Contributing

Contributions are welcome! Feel free to submit issues or pull requests for enhancements, bug fixes, or new features.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
