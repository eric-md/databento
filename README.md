# Trade Data Analysis and Charting Tool

This Python script fetches and analyzes trade data from Databento, creating detailed price analysis and interactive charts.

## Features

- Fetches trade data from Databento API
- Generates hourly price summaries (high/low)
- Calculates daily statistics including:
  - Day's price range
  - Total trading volume
  - Min/Max trade sizes
- Saves raw trade data to CSV
- Creates interactive charts using Plotly

## Prerequisites

- Python 3.x
- Databento API key

## Installation

1. Clone this repository:
```bash
git clone [your-repository-url]
cd [repository-name]
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Set up your Databento API key:
Replace the `API_KEY` variable in `trade_chart.py` with your Databento API key.

## Usage

Run the script from the command line:
```bash
python3 trade_chart.py
```

By default, the script analyzes PLTR (Palantir Technologies) data for a specific date. To analyze different symbols or dates, modify the following variables in the script:

```python
symbol = "PLTR"  # Change to your desired symbol
start_date = "2024-12-23"  # Change to your desired date
```

## Output

The script provides:
- Hourly price summaries
- Daily statistics
- Trade data saved to CSV file
- Interactive price charts

## Dependencies

- databento>=0.19.0
- pandas>=2.1.0
- plotly>=5.18.0

## Note

Make sure to keep your Databento API key secure and never commit it directly to the repository.
