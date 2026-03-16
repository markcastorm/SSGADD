# parser.py
# Parser for SSGA Option Adjusted Duration data and cumulative data management

import logging
from datetime import datetime
import pandas as pd
import config
import os
import re

# Setup logging
logger = logging.getLogger(__name__)


class SSGADDParser:
    """Parses SSGA ETF data and manages cumulative master data"""

    def __init__(self):
        self.debug = config.DEBUG_MODE
        self.logger = logger

    def parse_date(self, date_str):
        """
        Parse date string from various formats to standard format.
        Handles formats like "Jan 13 2026", "January 13 2026", etc.

        Returns datetime object or None if parsing fails.
        """

        if not date_str:
            return None

        date_str = date_str.strip()

        for date_format in config.INPUT_DATE_FORMATS:
            try:
                dt = datetime.strptime(date_str, date_format)
                return dt
            except ValueError:
                continue

        self.logger.warning(f"Could not parse date: {date_str}")
        return None

    def parse_duration_value(self, duration_str):
        """
        Parse duration value from string (e.g., "2.87 years" -> 2.87).
        Handles various formats: "2.87 years", "2.87", "2.87 year"

        Returns float or None if parsing fails.
        """

        if not duration_str or duration_str.strip() == '':
            return None

        try:
            # Remove "years", "year", whitespace
            duration_str = duration_str.strip().lower()
            duration_str = duration_str.replace('years', '').replace('year', '').strip()

            # Convert to float
            duration = float(duration_str)

            # Validate duration is within reasonable range
            if config.MIN_DURATION_VALUE <= duration <= config.MAX_DURATION_VALUE:
                return duration
            else:
                self.logger.warning(f"Duration {duration} years outside valid range")
                return None

        except ValueError:
            self.logger.warning(f"Could not parse duration value: {duration_str}")
            return None

    def parse_scraped_data(self, scraped_results):
        """
        Parse the scraped results from all products.

        Args:
            scraped_results: Dict with product keys and their scraped data

        Returns:
            dict with 'date', 'date_str', and 'durations' (keyed by column code)
        """

        self.logger.info("Parsing scraped data...")

        if not scraped_results:
            self.logger.error("No scraped results to parse")
            return None

        # All products should have the same date
        # Get date from first product
        first_product = list(scraped_results.keys())[0]
        date_str = scraped_results[first_product].get('date_str')

        if not date_str:
            self.logger.error("No date found in scraped data")
            return None

        # Parse the date
        date_obj = self.parse_date(date_str)

        if not date_obj:
            self.logger.error(f"Could not parse date: {date_str}")
            return None

        self.logger.info(f"Parsed date: {date_obj.strftime(config.DATE_FORMAT_OUTPUT)}")

        # Parse durations for each product
        durations = {}

        for col_info in config.OUTPUT_COLUMNS:
            product_key = col_info['url_key']
            code = col_info['code']

            if product_key not in scraped_results:
                self.logger.warning(f"Product {product_key} not in scraped results")
                durations[code] = None
                continue

            duration_str = scraped_results[product_key].get('duration_str')

            if not duration_str:
                self.logger.warning(f"No duration string for {product_key}")
                durations[code] = None
                continue

            duration = self.parse_duration_value(duration_str)

            if duration is not None:
                durations[code] = duration
                self.logger.info(f"{product_key}: {duration} years")
            else:
                self.logger.warning(f"Could not parse duration for {product_key}")
                durations[code] = None

        # Check if we have at least some valid durations
        valid_durations = [v for v in durations.values() if v is not None]

        if len(valid_durations) == 0:
            self.logger.error("No valid durations parsed")
            return None

        return {
            'date': date_obj,
            'date_str': date_obj.strftime(config.DATE_FORMAT_OUTPUT),
            'durations': durations
        }

    def load_master_data(self):
        """
        Load the master cumulative data file.
        Returns DataFrame or None if file doesn't exist.
        """

        # Load from the actual master file location (master_data folder)
        master_path = os.path.join(config.MASTER_DATA_DIR, config.MASTER_FILE_NAME)

        if not os.path.exists(master_path):
            self.logger.warning(f"Master data file not found: {master_path}")
            return None

        try:
            self.logger.info(f"Loading master data from {master_path}")

            # Read Excel file (skip first row which contains codes)
            df = pd.read_excel(master_path, sheet_name=0, header=1)

            # Rename first column to 'date'
            df.rename(columns={df.columns[0]: 'date'}, inplace=True)

            # Map description column names to code column names
            # (Master file uses descriptions as headers, but we need codes for consistency)
            desc_to_code = {}
            for col_info in config.OUTPUT_COLUMNS:
                desc_to_code[col_info['description']] = col_info['code']

            df.rename(columns=desc_to_code, inplace=True)

            # Convert date column to datetime
            df['date'] = pd.to_datetime(df['date'], errors='coerce')

            # Drop rows with invalid dates
            df = df.dropna(subset=['date'])

            # Sort by date
            df = df.sort_values('date')

            self.logger.info(f"Loaded {len(df)} rows from master data")
            return df

        except Exception as e:
            self.logger.error(f"Error loading master data: {e}")
            return None

    def get_latest_date_in_master(self, master_df):
        """Get the latest date in the master data"""

        if master_df is None or len(master_df) == 0:
            return None

        latest_date = master_df['date'].max()
        self.logger.info(f"Latest date in master: {latest_date.strftime(config.DATE_FORMAT_OUTPUT)}")
        return latest_date

    def is_new_data(self, scraped_date, latest_date_in_master):
        """
        Check if scraped date is newer than the latest date in master.

        Returns:
            True if data is new, False otherwise
        """

        if latest_date_in_master is None:
            self.logger.info("No existing master data - data is new")
            return True

        if scraped_date > latest_date_in_master:
            self.logger.info(f"New data detected: {scraped_date.strftime(config.DATE_FORMAT_OUTPUT)} > {latest_date_in_master.strftime(config.DATE_FORMAT_OUTPUT)}")
            return True
        else:
            self.logger.info(f"Data is not new: {scraped_date.strftime(config.DATE_FORMAT_OUTPUT)} <= {latest_date_in_master.strftime(config.DATE_FORMAT_OUTPUT)}")
            return False

    def merge_data(self, master_df, scraped_data):
        """
        Merge master data with new scraped data.
        Returns combined DataFrame.
        """

        self.logger.info("Merging master and scraped data...")

        # Convert scraped data to DataFrame
        if not scraped_data:
            self.logger.warning("No new scraped data to merge")
            return master_df

        # Build record for DataFrame
        record = {'date': scraped_data['date']}
        record.update(scraped_data['durations'])

        scraped_df = pd.DataFrame([record])

        # If no master data, return scraped data
        if master_df is None or len(master_df) == 0:
            self.logger.info("No master data - using scraped data only")
            return scraped_df

        # Combine master and scraped data
        combined_df = pd.concat([master_df, scraped_df], ignore_index=True)

        # Remove duplicates (keep last occurrence)
        combined_df = combined_df.drop_duplicates(subset=['date'], keep='last')

        # Sort by date
        combined_df = combined_df.sort_values('date')

        self.logger.info(f"Merged data: {len(combined_df)} total rows")
        return combined_df

    def parse_and_merge(self, scraped_results):
        """
        Main method to parse scraped data and merge with master data.
        Returns combined DataFrame ready for file generation.
        """

        # Parse scraped data
        scraped_data = self.parse_scraped_data(scraped_results)

        if not scraped_data:
            self.logger.error("No data parsed from scraped results")
            return None

        # Load master data
        master_df = self.load_master_data()

        # Get latest date in master
        latest_date = self.get_latest_date_in_master(master_df)

        # Check if data is new
        if config.REBUILD_MASTER:
            self.logger.info("REBUILD_MASTER is True - using all scraped data")
            new_data = scraped_data
        else:
            is_new = self.is_new_data(scraped_data['date'], latest_date)

            if not is_new:
                self.logger.warning("Scraped data is not newer than master - no update needed")
                self.logger.warning("Returning master data without changes")
                return master_df

            new_data = scraped_data

        # Merge data
        combined_df = self.merge_data(master_df, new_data)

        return combined_df


def main():
    """Test the parser with sample scraped data"""

    # Sample scraped results
    sample_results = {
        'JNK': {
            'product': 'JNK',
            'date_str': 'Jan 13 2026',
            'duration_str': '2.87 years'
        },
        'SPIB': {
            'product': 'SPIB',
            'date_str': 'Jan 13 2026',
            'duration_str': '4.01 years'
        }
    }

    parser = SSGADDParser()
    df = parser.parse_and_merge(sample_results)

    if df is not None:
        print(f"\nParsed {len(df)} rows")
        print(f"\nFirst 5 rows:")
        print(df.head())
        print(f"\nLast 5 rows:")
        print(df.tail())
    else:
        print("\n[FAILED] Could not parse data")


if __name__ == '__main__':
    main()
