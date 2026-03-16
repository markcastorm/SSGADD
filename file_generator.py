# file_generator.py
# Generate Excel DATA and META files for SSGADD dataset

import os
import zipfile
import logging
from datetime import datetime
import pandas as pd
import config

# Setup logging
logger = logging.getLogger(__name__)


class SSGADDFileGenerator:
    """Generates Excel DATA and META files in the required format"""

    def __init__(self):
        self.debug = config.DEBUG_MODE
        self.logger = logger

    def create_data_file(self, df, output_path):
        """
        Create the DATA Excel file with the exact column structure from config.

        Args:
            df: DataFrame with date column and duration columns
            output_path: Path to save the Excel file

        Returns:
            Path to created file
        """

        self.logger.info(f"Creating DATA file with {len(df)} records")

        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Create a copy of the DataFrame
            output_df = df.copy()

            # Ensure date column is first
            if 'date' not in output_df.columns:
                self.logger.error("DataFrame missing 'date' column")
                return None

            # Convert datetime to string format
            if pd.api.types.is_datetime64_any_dtype(output_df['date']):
                output_df['date'] = output_df['date'].dt.strftime(config.DATE_FORMAT_OUTPUT)

            # Reorder columns to match config.OUTPUT_COLUMNS
            column_order = ['date'] + [col['code'] for col in config.OUTPUT_COLUMNS]

            # Add missing columns as empty
            for col in column_order:
                if col not in output_df.columns and col != 'date':
                    output_df[col] = None

            # Select and reorder columns
            output_df = output_df[column_order]

            # Create writer object
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # Write headers first (Row 1: Codes)
                # First cell should be empty (not 'date')
                header_row = [''] + [col['code'] for col in config.OUTPUT_COLUMNS]
                header_df = pd.DataFrame([header_row])
                header_df.to_excel(writer, sheet_name='DATA', index=False, header=False, startrow=0)

                # Write descriptions (Row 2: Descriptions)
                descriptions = [''] + [col['description'] for col in config.OUTPUT_COLUMNS]
                desc_df = pd.DataFrame([descriptions])
                desc_df.to_excel(writer, sheet_name='DATA', index=False, header=False, startrow=1)

                # Write data (starting from Row 3)
                output_df.to_excel(writer, sheet_name='DATA', index=False, header=False, startrow=2)

            self.logger.info(f"DATA file saved: {output_path}")
            return output_path

        except Exception as e:
            self.logger.error(f"Error creating DATA file: {e}")
            return None

    def create_meta_file(self, output_path):
        """
        Create the META Excel file with metadata for all time series.

        Args:
            output_path: Path to save the Excel file

        Returns:
            Path to created file
        """

        self.logger.info("Creating META file")

        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Build metadata records
            meta_records = []

            for col_info in config.OUTPUT_COLUMNS:
                code = col_info['code']
                description = col_info['description']
                url = config.URLS[col_info['url_key']]

                # Extract CODE_MNEMONIC (part after the last dot before .B)
                # E.g., SSGADD.SPDRBBGBARCLAYSHIGHYIELDBONDETF.OPTADJDURATION.B -> SSGADD.SPDRBBGBARCLAYSHIGHYIELDBONDETF.OPTADJDURATION
                code_mnemonic = code.rsplit('.', 1)[0] if '.' in code else code

                record = {
                    'CODE': code,
                    'CODE_MNEMONIC': code_mnemonic,
                    'DESCRIPTION': description,
                    'FREQUENCY': config.METADATA_DEFAULTS['FREQUENCY'],
                    'MULTIPLIER': config.METADATA_DEFAULTS['MULTIPLIER'],
                    'AGGREGATION_TYPE': config.METADATA_DEFAULTS['AGGREGATION_TYPE'],
                    'UNIT_TYPE': config.METADATA_DEFAULTS['UNIT_TYPE'],
                    'DATA_TYPE': config.METADATA_DEFAULTS['DATA_TYPE'],
                    'DATA_UNIT': config.METADATA_DEFAULTS['DATA_UNIT'],
                    'SEASONALLY_ADJUSTED': config.METADATA_DEFAULTS['SEASONALLY_ADJUSTED'],
                    'ANNUALIZED': config.METADATA_DEFAULTS['ANNUALIZED'],
                    'STATE': config.METADATA_DEFAULTS['STATE'],
                    'PROVIDER_MEASURE_URL': url,
                    'PROVIDER': config.METADATA_DEFAULTS['PROVIDER'],
                    'SOURCE': config.METADATA_DEFAULTS['SOURCE'],
                    'SOURCE_DESCRIPTION': config.METADATA_DEFAULTS['SOURCE_DESCRIPTION'],
                    'COUNTRY': config.METADATA_DEFAULTS['COUNTRY'],
                    'DATASET': config.METADATA_DEFAULTS['DATASET']
                }

                meta_records.append(record)

            # Create DataFrame
            meta_df = pd.DataFrame(meta_records, columns=config.METADATA_COLUMNS)

            # Save to Excel
            meta_df.to_excel(output_path, index=False, sheet_name='META', engine='openpyxl')

            self.logger.info(f"META file saved: {output_path}")
            return output_path

        except Exception as e:
            self.logger.error(f"Error creating META file: {e}")
            return None

    def create_zip_file(self, data_file, meta_file, zip_path):
        """
        Create a ZIP file containing the DATA and META files.

        Args:
            data_file: Path to DATA file
            meta_file: Path to META file
            zip_path: Path for output ZIP file

        Returns:
            Path to created ZIP file
        """

        self.logger.info(f"Creating ZIP file: {zip_path}")

        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(zip_path), exist_ok=True)

            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add files with just their basename (no path)
                zipf.write(data_file, os.path.basename(data_file))
                zipf.write(meta_file, os.path.basename(meta_file))

            self.logger.info(f"ZIP file created: {zip_path}")
            return zip_path

        except Exception as e:
            self.logger.error(f"Error creating ZIP file: {e}")
            return None

    def save_master_data(self, df):
        """
        Save the updated master data file.

        Args:
            df: DataFrame with combined data

        Returns:
            Path to saved master file
        """

        self.logger.info("Saving updated master data file...")

        try:
            # Create master data directory
            os.makedirs(config.MASTER_DATA_DIR, exist_ok=True)

            master_path = os.path.join(config.MASTER_DATA_DIR, config.MASTER_FILE_NAME)

            # Prepare DataFrame (same structure as DATA file)
            output_df = df.copy()

            # Convert datetime to string format
            if pd.api.types.is_datetime64_any_dtype(output_df['date']):
                output_df['date'] = output_df['date'].dt.strftime(config.DATE_FORMAT_OUTPUT)

            # Ensure date column is first
            column_order = ['date'] + [col['code'] for col in config.OUTPUT_COLUMNS]

            # Add missing columns
            for col in column_order:
                if col not in output_df.columns and col != 'date':
                    output_df[col] = None

            # Select and reorder columns
            output_df = output_df[column_order]

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
                output_df.to_excel(writer, sheet_name='DATA', index=False, header=False, startrow=2)

            self.logger.info(f"Master data saved: {master_path}")
            return master_path

        except Exception as e:
            self.logger.error(f"Error saving master data: {e}")
            return None

    def generate_files(self, df):
        """
        Generate DATA, META, and ZIP files from DataFrame.

        Args:
            df: DataFrame with date and duration columns

        Returns:
            Dict with paths to created files
        """

        if df is None or len(df) == 0:
            self.logger.error("No data to generate files")
            return None

        # Generate filenames with timestamp
        timestamp = config.RUN_TIMESTAMP
        data_filename = config.DATA_FILE_PATTERN.format(timestamp=timestamp)
        meta_filename = config.META_FILE_PATTERN.format(timestamp=timestamp)
        zip_filename = config.ZIP_FILE_PATTERN.format(timestamp=timestamp)

        # Create output directory
        os.makedirs(config.OUTPUT_DIR, exist_ok=True)

        data_path = os.path.join(config.OUTPUT_DIR, data_filename)
        meta_path = os.path.join(config.OUTPUT_DIR, meta_filename)
        zip_path = os.path.join(config.OUTPUT_DIR, zip_filename)

        # Create files
        data_file = self.create_data_file(df, data_path)
        meta_file = self.create_meta_file(meta_path)

        if not data_file or not meta_file:
            self.logger.error("Failed to create DATA or META file")
            return None

        zip_file = self.create_zip_file(data_file, meta_file, zip_path)

        # Also copy to 'latest' folder
        latest_dir = config.LATEST_OUTPUT_DIR
        os.makedirs(latest_dir, exist_ok=True)

        latest_data_path = os.path.join(latest_dir, f"SSGADD_DATA_LATEST.xlsx")
        latest_meta_path = os.path.join(latest_dir, f"SSGADD_META_LATEST.xlsx")
        latest_zip_path = os.path.join(latest_dir, f"SSGADD_LATEST.zip")

        # Copy to latest folder
        import shutil
        shutil.copy2(data_path, latest_data_path)
        shutil.copy2(meta_path, latest_meta_path)
        if zip_file:
            shutil.copy2(zip_path, latest_zip_path)

        self.logger.info("Files also copied to 'latest' folder")

        # Save updated master data
        master_path = self.save_master_data(df)

        return {
            'data_file': data_path,
            'meta_file': meta_path,
            'zip_file': zip_file,
            'latest_data': latest_data_path,
            'latest_meta': latest_meta_path,
            'latest_zip': latest_zip_path,
            'master_file': master_path
        }


def main():
    """Test the file generator with sample data"""
    import pandas as pd

    # Sample data
    sample_data = {
        'date': ['2026-01-13', '2026-01-12', '2026-01-09'],
        'SSGADD.SPDRBBGBARCLAYSHIGHYIELDBONDETF.OPTADJDURATION.B': [2.87, 2.85, 2.90],
        'SSGADD.SPDRPORTFOLIOINTERMEDIATETERMCORPORATEBONDETF.OPTADJDURATION.B': [4.01, 4.00, 4.03]
    }

    df = pd.DataFrame(sample_data)

    generator = SSGADDFileGenerator()
    result = generator.generate_files(df)

    if result:
        print("\nGenerated files:")
        for key, path in result.items():
            print(f"  {key}: {path}")
    else:
        print("\n[FAILED] Could not generate files")


if __name__ == '__main__':
    main()
