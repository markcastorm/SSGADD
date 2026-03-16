# SSGADD - SSGA Option Adjusted Duration Data Collection

Automated data collection system for tracking Option Adjusted Duration values from State Street Global Advisors (SSGA) ETF products.

## Overview

This project scrapes Option Adjusted Duration data from two SSGA ETF pages:
- **JNK** - SPDR BBG Barclays High Yield Bond ETF
- **SPIB** - SPDR Portfolio Intermediate Term Corporate Bond ETF

The system maintains cumulative historical data, automatically detects new dates, and generates standardized Excel output files.

## Features

- ✅ **Automated Web Scraping** - Selenium-based scraper with cookie modal handling
- ✅ **Cumulative Data Tracking** - Master file stores all historical data
- ✅ **Incremental Updates** - Only appends new dates, no duplicates
- ✅ **Timestamped Outputs** - Each run creates a timestamped folder
- ✅ **Latest Folder** - Always maintains most recent data
- ✅ **Exact Column Structure** - Preserves exact header/subheader format
- ✅ **Comprehensive Logging** - Detailed logs for debugging

## Project Structure

```
SSGADD/
├── config.py                 # All configuration and mappings
├── scraper.py                # Web scraper (Selenium)
├── parser.py                 # Data parser and master data manager
├── file_generator.py         # Excel file generator (DATA, META, ZIP)
├── orchestrator.py           # Main execution script
├── initialize_master.py      # Initialize master from historical data
├── logger_setup.py           # Logging configuration
├── requirements.txt          # Python dependencies
├── README.md                 # This file
├── master_data/              # Master data storage
│   └── SSGADD_MASTER_DATA.xlsx
├── output/                   # Timestamped output folders
│   ├── 20260115_123456/      # Example timestamped run
│   └── latest/               # Always contains latest files
└── logs/                     # Timestamped log folders
    ├── 20260115_123456/
    └── latest/
```

## Installation

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install Chrome WebDriver

The scraper uses Selenium with Chrome. Make sure you have:
- Google Chrome installed
- ChromeDriver compatible with your Chrome version

Or use `webdriver-manager` (included in requirements.txt) for automatic driver management.

## Usage

### First Time Setup

Before running the orchestrator for the first time, initialize the master data file from your historical data:

```bash
python initialize_master.py
```

This will:
1. Read `Project information/SSGADD_DATA_20260114.xlsx`
2. Create the master data file in `master_data/SSGADD_MASTER_DATA.xlsx`
3. Prepare the system for incremental updates

### Regular Runs

After initialization, run the orchestrator to scrape and update data:

```bash
python orchestrator.py
```

This will:
1. Scrape both ETF pages for Option Adjusted Duration values
2. Extract the "as of" date
3. Check if the date is newer than the master file's latest date
4. If new, append data to master and generate output files
5. Save files to timestamped folder and "latest" folder

## Output Files

Each run generates three files:

### 1. DATA File (SSGADD_DATA_YYYYMMDD_HHMMSS.xlsx)
```
Row 1 (Codes):
  [Empty] | SSGADD.SPDRBBGBARCLAYSHIGHYIELDBONDETF.OPTADJDURATION.B | ...

Row 2 (Descriptions):
  [Empty] | SPDR BBG Barclays High Yield Bond ETF | ...

Row 3+ (Data):
  2024-03-08 | 3.22 | 4.06
  2024-03-11 | 3.21 | 4.05
  ...
```

### 2. META File (SSGADD_META_YYYYMMDD_HHMMSS.xlsx)
Contains metadata for each time series:
- CODE, DESCRIPTION, FREQUENCY, UNIT_TYPE, etc.

### 3. ZIP File (SSGADD_YYYYMMDD_HHMMSS.zip)
Contains both DATA and META files.

## Configuration

Key settings in [config.py](config.py):

### URLs
```python
URLS = {
    'JNK': 'https://www.ssga.com/us/en/intermediary/etfs/spdr-bloomberg-high-yield-bond-etf-jnk',
    'SPIB': 'https://www.ssga.com/us/en/intermediary/etfs/spdr-portfolio-intermediate-term-corporate-bond-etf-spib'
}
```

### Master Data File
```python
MASTER_DATA_FILE = r'D:\Projects\SIMBA-RUNBOOKS\SSGADD\Project information\SSGADD_DATA_20260114.xlsx'
```

### Browser Settings
```python
HEADLESS_MODE = True  # Set to False to see browser during scraping
DEBUG_MODE = True     # Enable detailed logging
```

## How It Works

### 1. Scraping Process
- Navigate to each ETF page
- Handle cookie consent modal (click "Accept and Save Cookies")
- Scroll to "Fund Characteristics" section
- Extract "as of" date (e.g., "as of Jan 13 2026")
- Extract "Option Adjusted Duration" value (e.g., "2.87 years")

### 2. Data Parsing
- Parse date strings (various formats supported)
- Parse duration values (remove "years" suffix)
- Validate data ranges

### 3. Master Data Management
- Load existing master file
- Check if scraped date is newer than latest date in master
- If new: append to master
- If not new: skip update

### 4. File Generation
- Create DATA file with exact column structure
- Create META file with metadata
- Create ZIP archive
- Copy to timestamped folder AND "latest" folder
- Update master data file

## Data Flow

```
[SSGA Websites]
      ↓
[Scraper] → Extract date & duration
      ↓
[Parser] → Parse & validate data
      ↓
[Master Data Check] → Is date new?
      ↓ (Yes)
[Merge with Master]
      ↓
[File Generator] → Create DATA, META, ZIP
      ↓
[Output Folders] → Timestamped + Latest
```

## Logging

Logs are saved to `logs/YYYYMMDD_HHMMSS/ssgadd_YYYYMMDD_HHMMSS.log`

Log levels:
- **DEBUG**: Detailed information for debugging
- **INFO**: General information about execution
- **WARNING**: Warnings (e.g., missing data)
- **ERROR**: Errors (e.g., failed scraping)

## Troubleshooting

### Issue: Cookie modal not detected
**Solution**: Increase `COOKIE_MODAL_WAIT` in config.py

### Issue: Fund Characteristics section not found
**Solution**: Check if website structure changed. Update selectors in config.py

### Issue: Date parsing fails
**Solution**: Website may use a different date format. Add format to `INPUT_DATE_FORMATS` in config.py

### Issue: ChromeDriver errors
**Solution**:
- Update Chrome browser
- Update chromedriver
- Or use `webdriver-manager` for automatic management

## Architecture Notes

This project follows the proven architecture from:
- CHEF_NOVARTIS (Novartis Pension Fund data collection)
- MNDMR_Runbook (Mortgage News Daily data collection)

Key design principles:
- **Modular**: Each component (scraper, parser, generator) is independent
- **Configurable**: All settings centralized in config.py
- **Cumulative**: Master file tracks all historical data
- **Incremental**: Only updates when new data is available
- **Robust**: Comprehensive error handling and logging

## License

Internal use only - AfricaAI

## Support

For issues or questions, contact the development team.
