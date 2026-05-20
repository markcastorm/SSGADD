# config.py
# SSGA Option Adjusted Duration Data Collection Configuration

import os
from datetime import datetime

# =============================================================================
# DATA SOURCE CONFIGURATION
# =============================================================================

# URLs for the two ETF products
URLS = {
    'JNK': 'https://www.ssga.com/us/en/intermediary/etfs/spdr-bloomberg-high-yield-bond-etf-jnk',
    'SPIB': 'https://www.ssga.com/us/en/intermediary/etfs/spdr-portfolio-intermediate-term-corporate-bond-etf-spib'
}

PROVIDER_NAME = 'State Street Global Advisors'
DATASET_NAME = 'SSGADD'
COUNTRY = 'USA'
CURRENCY = 'USD'

# =============================================================================
# TIMESTAMPED FOLDERS CONFIGURATION
# =============================================================================

# Generate timestamp for this run (format: YYYYMMDD_HHMMSS)
RUN_TIMESTAMP = datetime.now().strftime('%Y%m%d_%H%M%S')

# Use timestamped folders to avoid conflicts between runs
USE_TIMESTAMPED_FOLDERS = True

# =============================================================================
# CUMULATIVE DATA CONFIGURATION
# =============================================================================

# Master data file path (contains historical cumulative data)
MASTER_DATA_FILE = r'D:\Projects\SIMBA-RUNBOOKS\SSGADD\Project information\SSGADD_DATA_20260114.xlsx'

# When True, always rebuild master from scratch
# When False, append only new data to existing master
REBUILD_MASTER = False

# =============================================================================
# WEB SCRAPING SELECTORS
# =============================================================================

SELECTORS = {
    # Cookie modal
    'cookie_modal': 'div#ssmp-self-identifier-modal',
    'cookie_accept_button': 'button#js-ssmp-clrButtonLabel',

    # Fund Characteristics section
    'fund_characteristics_section': 'div.keyvalue.fundcomps',
    'section_title': 'h2.comp-title',
    'date_span': 'span.date',

    # Table with fund data
    'data_table': 'table.tb-keyvalue',
    'table_rows': 'tr',
    'label_cell': 'th.label',
    'data_cell': 'td.data',

    # Specific target
    'option_adjusted_duration_label': 'Option Adjusted Duration'
}

# =============================================================================
# OUTPUT COLUMN STRUCTURE (EXACT ORDER - DO NOT CHANGE)
# =============================================================================

# Based on SSGADD_DATA_20260114.xlsx
# Column order is ABSOLUTE and must match exactly

OUTPUT_COLUMNS = [
    {
        'code': 'SSGADD.SPDRBBGBARCLAYSHIGHYIELDBONDETF.OPTADJDURATION.B',
        'description': 'SPDR BBG Barclays High Yield Bond ETF',
        'product': 'JNK',
        'url_key': 'JNK',
        'unit': 'Years',
        'metric': 'Option Adjusted Duration'
    },
    {
        'code': 'SSGADD.SPDRPORTFOLIOINTERMEDIATETERMCORPORATEBONDETF.OPTADJDURATION.B',
        'description': 'SPDR Portfolio Intermediate Term Corporate Bond ETF',
        'product': 'SPIB',
        'url_key': 'SPIB',
        'unit': 'Years',
        'metric': 'Option Adjusted Duration'
    }
]

# =============================================================================
# METADATA STANDARD FIELDS
# =============================================================================

METADATA_DEFAULTS = {
    'FREQUENCY': 'B',  # Business daily
    'MULTIPLIER': 0,
    'AGGREGATION_TYPE': 'UNDEFINED',
    'UNIT_TYPE': 'LEVEL',
    'DATA_TYPE': 'DURATION',
    'DATA_UNIT': 'YEARS',
    'SEASONALLY_ADJUSTED': 'NSA',
    'ANNUALIZED': 'FALSE',
    'STATE': 'ACTIVE',
    'PROVIDER': 'AfricaAI',
    'SOURCE': 'SSGA',
    'SOURCE_DESCRIPTION': PROVIDER_NAME,
    'COUNTRY': COUNTRY,
    'DATASET': DATASET_NAME
}

# Metadata file columns
METADATA_COLUMNS = [
    'CODE',
    'CODE_MNEMONIC',
    'DESCRIPTION',
    'FREQUENCY',
    'MULTIPLIER',
    'AGGREGATION_TYPE',
    'UNIT_TYPE',
    'DATA_TYPE',
    'DATA_UNIT',
    'SEASONALLY_ADJUSTED',
    'ANNUALIZED',
    'STATE',
    'PROVIDER_MEASURE_URL',
    'PROVIDER',
    'SOURCE',
    'SOURCE_DESCRIPTION',
    'COUNTRY',
    'DATASET'
]

# =============================================================================
# DATE FORMATS
# =============================================================================

# Input date formats (from website "as of Jan 13 2026")
INPUT_DATE_FORMATS = [
    '%b %d %Y',      # Jan 13 2026
    '%B %d %Y',      # January 13 2026
    '%m/%d/%Y',      # 1/13/2026
    '%Y-%m-%d'       # 2026-01-13
]

# Output date format
DATE_FORMAT_OUTPUT = '%Y-%m-%d'  # 2026-01-13

# Filename date format
FILENAME_DATE_FORMAT = '%Y%m%d'

# Log date format
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# =============================================================================
# BROWSER CONFIGURATION
# =============================================================================

HEADLESS_MODE = False
DEBUG_MODE = True
WAIT_TIMEOUT = 20
PAGE_LOAD_DELAY = 3
SCROLL_DELAY = 2  # Time to wait after scrolling to Fund Characteristics section
COOKIE_MODAL_WAIT = 5  # Wait time for cookie modal to appear

# =============================================================================
# OUTPUT CONFIGURATION
# =============================================================================

# Base directories
BASE_OUTPUT_DIR = './output'
BASE_LOG_DIR = './logs'

# Apply timestamping if enabled
if USE_TIMESTAMPED_FOLDERS:
    OUTPUT_DIR = os.path.join(BASE_OUTPUT_DIR, RUN_TIMESTAMP)
    LOG_DIR = os.path.join(BASE_LOG_DIR, RUN_TIMESTAMP)
else:
    OUTPUT_DIR = BASE_OUTPUT_DIR
    LOG_DIR = BASE_LOG_DIR

# Latest folder (always contains most recent extraction)
LATEST_OUTPUT_DIR = os.path.join(BASE_OUTPUT_DIR, 'latest')

# Master data directory (where cumulative master file is stored)
MASTER_DATA_DIR = './master_data'

# File naming patterns
DATA_FILE_PATTERN = 'SSGADD_DATA_{timestamp}.xlsx'
META_FILE_PATTERN = 'SSGADD_META_{timestamp}.xlsx'
ZIP_FILE_PATTERN = 'SSGADD_{timestamp}.zip'

# Master file naming
MASTER_FILE_NAME = 'SSGADD_MASTER_DATA.xlsx'

# Log file naming
LOG_FILE_PATTERN = 'ssgadd_{timestamp}.log'

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

# Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL = 'DEBUG' if DEBUG_MODE else 'INFO'

# Log format
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Console output
LOG_TO_CONSOLE = True
LOG_TO_FILE = True

# =============================================================================
# VALIDATION SETTINGS
# =============================================================================

# Validate that all required products are found
REQUIRE_ALL_PRODUCTS = True

# Validate duration values (should be reasonable years)
MIN_DURATION_VALUE = 0.1  # Minimum 0.1 years
MAX_DURATION_VALUE = 30.0  # Maximum 30 years

# =============================================================================
# ERROR HANDLING
# =============================================================================

# Continue processing even if some products fail
CONTINUE_ON_ERROR = True

# Maximum retries for page load failures
MAX_RETRIES = 3
RETRY_DELAY = 5.0  # Seconds between retries
