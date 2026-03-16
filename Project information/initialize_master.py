#!/usr/bin/env python3
# initialize_master.py
# Initialize master data file from existing historical Excel file

import os
import pandas as pd
import config
from logger_setup import setup_logging
import logging

logger = logging.getLogger(__name__)


def initialize_master_from_historical():
    """
    Initialize master data file from existing historical Excel file.
    Reads SSGADD_DATA_20260114.xlsx and creates the master file.
    """

    setup_logging()

    print("\n" + "="*70)
    print(" Initialize Master Data File")
    print("="*70 + "\n")

    # Source file (your existing historical data)
    source_file = config.MASTER_DATA_FILE

    if not os.path.exists(source_file):
        print(f"[ERROR] Source file not found: {source_file}")
        print("Please ensure SSGADD_DATA_20260114.xlsx is in the correct location.")
        return False

    print(f"Source file: {source_file}")

    try:
        # Read the existing Excel file
        print("\nReading existing historical data...")

        # Read Excel, skipping first row (codes), using second row as header
        df = pd.read_excel(source_file, sheet_name=0, header=1)

        print(f"  Loaded {len(df)} rows")

        # Rename first column to 'date'
        df.rename(columns={df.columns[0]: 'date'}, inplace=True)

        # Convert date column to datetime
        df['date'] = pd.to_datetime(df['date'], errors='coerce')

        # Drop rows with invalid dates
        df = df.dropna(subset=['date'])

        # Convert date to string format for output
        df['date'] = df['date'].dt.strftime(config.DATE_FORMAT_OUTPUT)

        # Sort by date
        df = df.sort_values('date')

        print(f"  Date range: {df['date'].min()} to {df['date'].max()}")
        print(f"  Valid records: {len(df)}")

        # Map description column names to code column names
        print("\nMapping columns from descriptions to codes...")

        # Create mapping from description to code
        desc_to_code = {}
        for col_info in config.OUTPUT_COLUMNS:
            desc_to_code[col_info['description']] = col_info['code']

        # Rename columns
        df.rename(columns=desc_to_code, inplace=True)

        # Ensure all required columns exist
        column_order = ['date'] + [col['code'] for col in config.OUTPUT_COLUMNS]

        for col in column_order:
            if col not in df.columns and col != 'date':
                df[col] = None
                print(f"  Warning: Missing data for column: {col}")

        # Select and reorder columns
        df = df[column_order]

        # Create master data directory
        os.makedirs(config.MASTER_DATA_DIR, exist_ok=True)

        master_path = os.path.join(config.MASTER_DATA_DIR, config.MASTER_FILE_NAME)

        print(f"\nSaving master file to: {master_path}")

        # Save with same structure as DATA file
        with pd.ExcelWriter(master_path, engine='openpyxl') as writer:
            # Write headers (Row 1: Codes)
            # First cell should be empty (not 'date')
            header_row = [''] + [col['code'] for col in config.OUTPUT_COLUMNS]
            header_df = pd.DataFrame([header_row])
            header_df.to_excel(writer, sheet_name='DATA', index=False, header=False, startrow=0)

            # Write descriptions (Row 2: Descriptions)
            descriptions = [''] + [col['description'] for col in config.OUTPUT_COLUMNS]
            desc_df = pd.DataFrame([descriptions])
            desc_df.to_excel(writer, sheet_name='DATA', index=False, header=False, startrow=1)

            # Write data (starting from Row 3)
            df.to_excel(writer, sheet_name='DATA', index=False, header=False, startrow=2)

        print(f"\n[SUCCESS] Master file created!")
        print(f"  Location: {master_path}")
        print(f"  Records: {len(df)}")
        print(f"  Latest date: {df['date'].max()}")

        print("\n" + "="*70)
        print(" Master file is ready!")
        print(" You can now run: python orchestrator.py")
        print("="*70 + "\n")

        logger.info(f"Master file initialized with {len(df)} records")

        return True

    except Exception as e:
        print(f"\n[ERROR] Failed to create master file: {e}")
        logger.exception("Error initializing master file")
        return False


if __name__ == '__main__':
    initialize_master_from_historical()
