# NASDAQ-100 Scraper

A Python tool for retrieving and storing current NASDAQ-100 constituents from Wikipedia.

## Description

This project scrapes the list of NASDAQ-100 companies from the Wikipedia page and saves the data in CSV and JSON formats. The tool uses multiple fallback strategies to ensure reliable data extraction.

## Features

- **Multiple extraction methods**: Uses both `pandas.read_html()` and `BeautifulSoup` as fallback
- **Robust error handling**: Automatic retry attempts on failures
- **Data validation**: Checks completeness and correctness of extracted data
- **Multiple output formats**: Saves data as both CSV and JSON
- **Logging**: Detailed logging of all operations
- **Data cleaning**: Automatic cleaning of whitespace and formatting

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd nasdaq100-scraper
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the script directly:

```bash
python nasdaq100_scraper.py
```

The tool will automatically:
1. Retrieve NASDAQ-100 data from Wikipedia
2. Validate and clean the data
3. Save results to `data/nasdaq100_constituents.csv` and `data/nasdaq100_constituents.json`
4. Display a summary of the first 5 entries

## Output Files

- **CSV format** (`data/nasdaq100_constituents.csv`): Tabular representation for Excel/spreadsheet programs
- **JSON format** (`data/nasdaq100_constituents.json`): Structured data for programmatic use

## Data Structure

The extracted data contains the following columns:
- **Ticker**: Company stock symbol
- **Company**: Full company name
- **GICS_Sector**: Global Industry Classification Standard sector
- **GICS_Sub_Industry**: GICS sub-industry

## Sample Data

The tool currently extracts 101 companies, including:
- Apple Inc. (AAPL) - Information Technology
- Microsoft (MSFT) - Information Technology
- Amazon (AMZN) - Consumer Discretionary
- Nvidia (NVDA) - Information Technology
- Meta Platforms (META) - Communication Services

## Technical Details

### Extraction Methods

1. **Pandas method**: First attempts `pandas.read_html()` for fast table extraction
2. **BeautifulSoup fallback**: Uses BeautifulSoup when pandas method fails
3. **Intelligent column detection**: Automatic identification of relevant table columns
4. **Retry mechanism**: Up to 3 retry attempts on network errors

### Data Validation

- Checks for at least 90 companies (typically ~100-101)
- Validates all required columns
- Cleans whitespace and formatting errors
- Ticker validation (1-5 uppercase letters)

## Dependencies

- `pandas>=1.3.0`: Data manipulation and CSV export
- `requests>=2.25.0`: HTTP requests
- `beautifulsoup4>=4.9.0`: HTML parsing as fallback
- `lxml>=4.6.0`: XML/HTML parser for pandas
- `html5lib>=1.1`: Additional HTML parser

## License and Data Sources

### Data Sources
The data is retrieved from the Wikipedia "NASDAQ-100" page:
- **Primary Source**: [Wikipedia - NASDAQ-100](https://en.wikipedia.org/wiki/Nasdaq-100)
- **Original Data Source**: Wikipedia references the official NASDAQ composition from [NASDAQ NDX Index](https://www.nasdaq.com/market-activity/quotes/nasdaq-ndx-index) (as of 2025-06-22)
- **License**: Wikipedia content is available under the [Creative Commons Attribution-ShareAlike License 3.0 (CC BY-SA 3.0)](https://creativecommons.org/licenses/by-sa/3.0/)

### Usage Notes for Wikipedia Data
- Data originates from Wikipedia and is subject to CC BY-SA 3.0 license
- When redistributing, Wikipedia must be credited as the source
- Derivative works must be published under the same license
- Data is provided "as is" without warranty for completeness or accuracy
- For financial decisions, please consult official sources

### Data Chain
The data flow is: **NASDAQ Official** → **Wikipedia** → **This Tool**
- NASDAQ maintains the official index composition at nasdaq.com
- Wikipedia editors update their page based on official NASDAQ data
- This tool extracts the data from Wikipedia for programmatic use

## Troubleshooting

### Common Issues

1. **Network errors**: The tool automatically retries on temporary connection problems
2. **Table structure changed**: If Wikipedia page changes, column detection logic may need adjustment
3. **Missing dependencies**: Ensure all packages from `requirements.txt` are installed

### Debug Information

The tool logs all steps in detail. For issues, check console output for specific error messages.

### Typical Output
```text
2025-06-22 08:27:58,468 - INFO - Attempt 1 of 3
2025-06-22 08:27:58,468 - INFO - Trying to retrieve data with pandas.read_html()...
2025-06-22 08:27:58,750 - WARNING - No suitable Components table found with pandas
2025-06-22 08:27:58,750 - INFO - Falling back to BeautifulSoup...
2025-06-22 08:27:59,078 - INFO - DataFrame validation successful
2025-06-22 08:27:59,078 - INFO - Successfully retrieved 101 components with BeautifulSoup
```

## Project Structure

```text
nasdaq100-scraper/
├── nasdaq100_scraper.py    # Main script
├── requirements.txt        # Python dependencies
├── README.md              # This file
└── data/                  # Output directory
    ├── nasdaq100_constituents.csv
    └── nasdaq100_constituents.json
```

## Contributing

Improvements and bug fixes are welcome! Please create a pull request or open an issue.

## Disclaimer

This tool is for informational purposes only. The data comes from Wikipedia and may be incomplete or outdated. For investment decisions, please consult official financial sources such as NASDAQ or Bloomberg.
