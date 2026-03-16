#!/usr/bin/env python3
# orchestrator.py
# Main orchestrator for SSGADD data collection

import os
import sys
from datetime import datetime
import config
from logger_setup import setup_logging
from scraper import SSGADDScraper
from parser import SSGADDParser
from file_generator import SSGADDFileGenerator
import logging

logger = logging.getLogger(__name__)


def print_banner():
    """Print a welcome banner"""
    print("\n" + "="*70)
    print(" SSGA ETF - Option Adjusted Duration Data Collection System")
    print(" Tracking SPDR ETF Duration Data - Cumulative Data Tracking")
    print("="*70 + "\n")


def print_configuration():
    """Print current configuration"""
    print("Configuration:")
    print("-" * 70)
    print(f"  Products: {len(config.OUTPUT_COLUMNS)}")
    for col_info in config.OUTPUT_COLUMNS:
        print(f"    - {col_info['product']}: {col_info['description']}")
    print(f"  Output: {config.OUTPUT_DIR}")
    print(f"  Master Data Dir: {config.MASTER_DATA_DIR}")
    print(f"  Rebuild Master: {'Yes' if config.REBUILD_MASTER else 'No'}")
    print(f"  Timestamp: {config.RUN_TIMESTAMP}")
    print("-" * 70 + "\n")


def main():
    """Main execution flow"""

    try:
        # Setup logging
        setup_logging()

        print_banner()
        print_configuration()

        # Step 1: Scrape ETF data
        print("STEP 1: Scraping ETF Data from SSGA Website")
        print("="*70 + "\n")

        scraper = SSGADDScraper()
        scraped_results = scraper.scrape_all_products()

        if not scraped_results:
            logger.error("Failed to scrape ETF data")
            print("\n[ERROR] Failed to scrape ETF data. Exiting.")
            sys.exit(1)

        print(f"[SUCCESS] Scraped data from {len(scraped_results)} products\n")

        # Display scraped data
        for product, data in scraped_results.items():
            print(f"  {product}:")
            print(f"    Date: {data.get('date_str')}")
            print(f"    Duration: {data.get('duration_str')}")

        logger.info(f"Successfully scraped {len(scraped_results)} products")

        # Step 2: Parse data and merge with master data
        print("\nSTEP 2: Parsing Data and Merging with Master Data")
        print("="*70 + "\n")

        parser = SSGADDParser()
        combined_df = parser.parse_and_merge(scraped_results)

        if combined_df is None or len(combined_df) == 0:
            logger.error("No data was parsed or merged")
            print("\n[ERROR] No data was parsed or merged. Exiting.")
            sys.exit(1)

        print(f"[SUCCESS] Parsed and merged data: {len(combined_df)} total rows")

        # Show date range
        if 'date' in combined_df.columns:
            dates = combined_df['date'].dropna()
            if len(dates) > 0:
                min_date = dates.min()
                max_date = dates.max()
                print(f"  Date range: {min_date} to {max_date}")

        # Show sample data
        print(f"\n  Latest 3 rows:")
        print(combined_df.tail(3).to_string(index=False))
        print()

        logger.info(f"Successfully merged {len(combined_df)} rows")

        # Step 3: Generate output files
        print("\nSTEP 3: Generating Excel Output Files")
        print("="*70 + "\n")

        generator = SSGADDFileGenerator()
        output_files = generator.generate_files(combined_df)

        if not output_files:
            logger.error("Failed to generate output files")
            print("\n[ERROR] Failed to generate output files. Exiting.")
            sys.exit(1)

        # Step 4: Summary
        print("\n" + "="*70)
        print(" EXECUTION COMPLETE")
        print("="*70 + "\n")

        print("Summary:")
        print(f"  Total records: {len(combined_df)}")

        # Count products with data
        products_with_data = 0
        for col_info in config.OUTPUT_COLUMNS:
            if col_info['code'] in combined_df.columns:
                non_null = combined_df[col_info['code']].notna().sum()
                if non_null > 0:
                    products_with_data += 1

        print(f"  Products tracked: {products_with_data} of {len(config.OUTPUT_COLUMNS)}")
        print()

        print("Output files:")
        print(f"  DATA: {os.path.basename(output_files['data_file'])}")
        print(f"  META: {os.path.basename(output_files['meta_file'])}")
        if output_files['zip_file']:
            print(f"  ZIP:  {os.path.basename(output_files['zip_file'])}")
        print()

        print(f"Output directory: {os.path.dirname(output_files['data_file'])}")
        print(f"Latest files: {config.LATEST_OUTPUT_DIR}")
        if output_files.get('master_file'):
            print(f"Master data: {output_files['master_file']}")
        print()

        print("="*70 + "\n")

        logger.info("Orchestrator completed successfully")

        return 0

    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Process interrupted by user")
        logger.warning("Process interrupted by user")
        sys.exit(130)

    except Exception as e:
        print(f"\n[ERROR] An unexpected error occurred: {e}")
        logger.exception("Unexpected error in orchestrator")
        sys.exit(1)


if __name__ == '__main__':
    sys.exit(main())
