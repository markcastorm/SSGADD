# scraper.py
# Web scraper for SSGA ETF Option Adjusted Duration data

import time
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import config

# Setup logging
logger = logging.getLogger(__name__)


class SSGADDScraper:
    """Scrapes Option Adjusted Duration data from SSGA ETF pages"""

    def __init__(self):
        self.driver = None
        self.logger = logger

    def setup_driver(self):
        """Initialize Chrome driver"""

        chrome_options = Options()

        if config.HEADLESS_MODE:
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--disable-gpu')

        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.set_page_load_timeout(config.WAIT_TIMEOUT)

        self.logger.info("Chrome driver initialized")

    def handle_cookie_modal(self):
        """
        Handle the SSGA cookie consent modal.
        Clicks the "Accept and Save Cookies" button.
        """

        self.logger.info("Checking for cookie modal...")

        try:
            # Wait for cookie modal to appear
            wait = WebDriverWait(self.driver, config.COOKIE_MODAL_WAIT)

            # Look for the modal
            modal = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, config.SELECTORS['cookie_modal']))
            )

            self.logger.info("Cookie modal detected")

            # Find and click the accept button
            accept_button = self.driver.find_element(By.CSS_SELECTOR, config.SELECTORS['cookie_accept_button'])

            if accept_button:
                accept_button.click()
                self.logger.info("Clicked 'Accept and Save Cookies' button")
                time.sleep(2)  # Wait for modal to close
                return True

        except TimeoutException:
            self.logger.info("No cookie modal appeared (may have been accepted previously)")
            return True
        except Exception as e:
            self.logger.warning(f"Error handling cookie modal: {e}")
            return False

    def navigate_to_page(self, url):
        """Navigate to the ETF page"""

        self.logger.info(f"Navigating to {url}")

        try:
            self.driver.get(url)
            time.sleep(config.PAGE_LOAD_DELAY)
            self.logger.info("Page loaded successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error loading page: {e}")
            return False

    def scroll_to_fund_characteristics(self):
        """Scroll down to Fund Characteristics section"""

        self.logger.info("Scrolling to Fund Characteristics section...")

        try:
            # Find the Fund Characteristics section
            sections = self.driver.find_elements(By.CSS_SELECTOR, config.SELECTORS['fund_characteristics_section'])

            for section in sections:
                title = section.find_element(By.CSS_SELECTOR, config.SELECTORS['section_title'])
                if 'Fund Characteristics' in title.text:
                    # Scroll element into view
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                        section
                    )
                    time.sleep(config.SCROLL_DELAY)
                    self.logger.info("Scrolled to Fund Characteristics section")
                    return True

            self.logger.warning("Fund Characteristics section not found")
            return False

        except Exception as e:
            self.logger.error(f"Error scrolling to section: {e}")
            return False

    def extract_fund_data(self, product_key):
        """
        Extract the "as of" date and Option Adjusted Duration value.

        Args:
            product_key: Product identifier (JNK or SPIB)

        Returns:
            dict with 'date', 'duration', and 'raw_html'
        """

        self.logger.info(f"Extracting fund data for {product_key}...")

        try:
            # Find the Fund Characteristics section
            sections = self.driver.find_elements(By.CSS_SELECTOR, config.SELECTORS['fund_characteristics_section'])

            for section in sections:
                title_elem = section.find_element(By.CSS_SELECTOR, config.SELECTORS['section_title'])

                if 'Fund Characteristics' in title_elem.text:
                    # Extract the "as of" date
                    date_str = None
                    try:
                        date_span = title_elem.find_element(By.CSS_SELECTOR, config.SELECTORS['date_span'])
                        date_str = date_span.text.strip()
                        # Remove "as of " prefix if present
                        if date_str.lower().startswith('as of '):
                            date_str = date_str[6:].strip()
                        self.logger.info(f"Found date: {date_str}")
                    except NoSuchElementException:
                        self.logger.warning("Could not find date span")

                    # Extract Option Adjusted Duration
                    table = section.find_element(By.CSS_SELECTOR, config.SELECTORS['data_table'])
                    rows = table.find_elements(By.CSS_SELECTOR, config.SELECTORS['table_rows'])

                    for row in rows:
                        try:
                            label_cell = row.find_element(By.CSS_SELECTOR, config.SELECTORS['label_cell'])
                            label_text = label_cell.text.strip()

                            # Check if this is the Option Adjusted Duration row
                            if config.SELECTORS['option_adjusted_duration_label'] in label_text:
                                data_cell = row.find_element(By.CSS_SELECTOR, config.SELECTORS['data_cell'])
                                duration_str = data_cell.text.strip()

                                self.logger.info(f"Found Option Adjusted Duration: {duration_str}")

                                # Get the HTML for debugging
                                section_html = section.get_attribute('outerHTML')

                                return {
                                    'product': product_key,
                                    'date_str': date_str,
                                    'duration_str': duration_str,
                                    'raw_html': section_html
                                }

                        except NoSuchElementException:
                            continue

            self.logger.error(f"Could not find Option Adjusted Duration for {product_key}")
            return None

        except Exception as e:
            self.logger.error(f"Error extracting fund data: {e}")
            return None

    def scrape_product(self, product_key, url):
        """
        Scrape data for a single product.

        Args:
            product_key: Product identifier (JNK or SPIB)
            url: URL to scrape

        Returns:
            dict with scraped data or None
        """

        self.logger.info(f"\n{'='*70}")
        self.logger.info(f"Scraping {product_key}: {url}")
        self.logger.info(f"{'='*70}")

        try:
            # Navigate to page
            if not self.navigate_to_page(url):
                self.logger.error(f"Failed to load page for {product_key}")
                return None

            # Handle cookie modal (only needed on first page)
            if product_key == 'JNK':  # Only handle on first product
                self.handle_cookie_modal()

            # Scroll to Fund Characteristics section
            if not self.scroll_to_fund_characteristics():
                self.logger.warning(f"Could not scroll to Fund Characteristics for {product_key}")

            # Extract data
            data = self.extract_fund_data(product_key)

            if data:
                self.logger.info(f"Successfully scraped {product_key}")
                return data
            else:
                self.logger.error(f"Failed to extract data for {product_key}")
                return None

        except Exception as e:
            self.logger.error(f"Error scraping {product_key}: {e}")
            return None

    def scrape_all_products(self):
        """
        Main method to scrape all ETF products.
        Returns dict with data for all products.
        """

        try:
            self.setup_driver()

            results = {}

            # Scrape each product in order
            for col_info in config.OUTPUT_COLUMNS:
                product_key = col_info['url_key']
                url = config.URLS[product_key]

                data = self.scrape_product(product_key, url)

                if data:
                    results[product_key] = data
                elif config.REQUIRE_ALL_PRODUCTS:
                    self.logger.error(f"Required product {product_key} failed - aborting")
                    return None

            if len(results) == 0:
                self.logger.error("No products were successfully scraped")
                return None

            self.logger.info(f"\nSuccessfully scraped {len(results)} products")
            return results

        except Exception as e:
            self.logger.error(f"Error during scraping: {e}")
            return None

        finally:
            if self.driver:
                self.driver.quit()
                self.logger.info("Browser closed")


def main():
    """Test the scraper"""
    scraper = SSGADDScraper()
    results = scraper.scrape_all_products()

    if results:
        print("\n[SUCCESS] Data extracted")
        for product, data in results.items():
            print(f"\n{product}:")
            print(f"  Date: {data.get('date_str')}")
            print(f"  Duration: {data.get('duration_str')}")
    else:
        print("\n[FAILED] Could not extract data")


if __name__ == '__main__':
    main()
