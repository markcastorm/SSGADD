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
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException,
    StaleElementReferenceException,
)
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

    def _get_element_text(self, element):
        """
        Get text from an element using multiple strategies.
        Selenium's .text can return empty if the element is not fully visible.
        Falls back to textContent/innerText via JavaScript.
        """
        text = element.text.strip()
        if text:
            return text

        # Fallback: use JavaScript to get textContent
        text = self.driver.execute_script(
            "return arguments[0].textContent;", element
        )
        if text:
            return text.strip()

        # Fallback: use innerText
        text = self.driver.execute_script(
            "return arguments[0].innerText;", element
        )
        return text.strip() if text else ''

    def _js_click(self, element):
        """Click an element via JavaScript (bypasses overlays)."""
        self.driver.execute_script("arguments[0].click();", element)

    def handle_cookie_modal(self):
        """
        Handle the SSGA cookie/self-identifier consent modal.
        Waits for the modal, clicks "Accept and Save Cookies",
        and waits for the modal to fully disappear before continuing.
        """

        self.logger.info("Checking for cookie modal...")

        try:
            wait = WebDriverWait(self.driver, config.COOKIE_MODAL_WAIT)

            # Wait for modal to be visible
            modal = wait.until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, config.SELECTORS['cookie_modal']))
            )
            self.logger.info("Cookie modal detected")

            # Wait for the accept button to be clickable
            accept_button = WebDriverWait(self.driver, config.COOKIE_MODAL_WAIT).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, config.SELECTORS['cookie_accept_button']))
            )

            # Try normal click first, fall back to JS click
            try:
                accept_button.click()
            except ElementClickInterceptedException:
                self.logger.info("Normal click intercepted, using JS click")
                self._js_click(accept_button)

            self.logger.info("Clicked 'Accept and Save Cookies' button")

            # Wait for the modal to fully disappear
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.invisibility_of_element_located((By.CSS_SELECTOR, config.SELECTORS['cookie_modal']))
                )
                self.logger.info("Cookie modal dismissed successfully")
            except TimeoutException:
                self.logger.warning("Modal did not disappear, attempting to continue anyway")

            return True

        except TimeoutException:
            self.logger.info("No cookie modal appeared (may have been accepted previously)")
            return True
        except Exception as e:
            self.logger.warning(f"Error handling cookie modal: {e}")
            return False

    def navigate_to_page(self, url):
        """Navigate to the ETF page and handle any modal that appears."""

        self.logger.info(f"Navigating to {url}")

        try:
            self.driver.get(url)
            time.sleep(config.PAGE_LOAD_DELAY)
            self.logger.info("Page loaded successfully")

            # Handle cookie modal on every page load (it can reappear)
            self.handle_cookie_modal()

            return True

        except Exception as e:
            self.logger.error(f"Error loading page: {e}")
            return False

    def _wait_for_fund_characteristics(self):
        """
        Wait for Fund Characteristics section to be present and visible.
        Returns the matching section element or None.
        """
        try:
            wait = WebDriverWait(self.driver, config.WAIT_TIMEOUT)
            sections = wait.until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, config.SELECTORS['fund_characteristics_section'])
                )
            )

            for section in sections:
                try:
                    title = section.find_element(By.CSS_SELECTOR, config.SELECTORS['section_title'])
                except NoSuchElementException:
                    continue

                title_text = self._get_element_text(title)
                if 'Fund Characteristics' in title_text:
                    return section

        except TimeoutException:
            self.logger.warning("Timed out waiting for fund sections to load")
        except Exception as e:
            self.logger.warning(f"Error waiting for fund characteristics: {e}")

        return None

    def scroll_to_fund_characteristics(self):
        """Scroll down to Fund Characteristics section"""

        self.logger.info("Scrolling to Fund Characteristics section...")

        section = self._wait_for_fund_characteristics()
        if section:
            self.driver.execute_script(
                "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                section
            )
            time.sleep(config.SCROLL_DELAY)
            self.logger.info("Scrolled to Fund Characteristics section")
            return True

        self.logger.warning("Fund Characteristics section not found")
        return False

    def extract_fund_data(self, product_key):
        """
        Extract the "as of" date and Option Adjusted Duration value.

        Uses multiple strategies:
        1. Selenium element text
        2. JavaScript textContent fallback
        3. BeautifulSoup HTML parsing as final fallback
        """

        self.logger.info(f"Extracting fund data for {product_key}...")

        # Strategy 1: Selenium with text fallbacks
        data = self._extract_via_selenium(product_key)
        if data:
            return data

        # Strategy 2: Parse page source with BeautifulSoup as fallback
        self.logger.info(f"Selenium extraction failed, trying BeautifulSoup fallback for {product_key}")
        data = self._extract_via_beautifulsoup(product_key)
        if data:
            return data

        self.logger.error(f"Could not find Option Adjusted Duration for {product_key}")
        return None

    def _extract_via_selenium(self, product_key):
        """Extract fund data using Selenium elements with text fallbacks."""
        try:
            section = self._wait_for_fund_characteristics()
            if not section:
                return None

            title_elem = section.find_element(By.CSS_SELECTOR, config.SELECTORS['section_title'])

            # Extract the "as of" date
            date_str = None
            try:
                date_span = title_elem.find_element(By.CSS_SELECTOR, config.SELECTORS['date_span'])
                date_str = self._get_element_text(date_span)
                if date_str.lower().startswith('as of '):
                    date_str = date_str[6:].strip()
                self.logger.info(f"Found date: {date_str}")
            except NoSuchElementException:
                self.logger.warning("Could not find date span")

            # Extract Option Adjusted Duration from table
            table = section.find_element(By.CSS_SELECTOR, config.SELECTORS['data_table'])
            rows = table.find_elements(By.CSS_SELECTOR, config.SELECTORS['table_rows'])

            target_label = config.SELECTORS['option_adjusted_duration_label']

            for row in rows:
                try:
                    # Try configured selector first, then fallback to th or td
                    label_cell = None
                    for selector in [config.SELECTORS['label_cell'], 'th.label', 'td.label', 'th', 'td:first-child']:
                        try:
                            label_cell = row.find_element(By.CSS_SELECTOR, selector)
                            break
                        except NoSuchElementException:
                            continue

                    if not label_cell:
                        continue

                    label_text = self._get_element_text(label_cell)

                    if target_label in label_text:
                        # Try configured selector first, then fallbacks
                        data_cell = None
                        for selector in [config.SELECTORS['data_cell'], 'td.data', 'td:last-child']:
                            try:
                                data_cell = row.find_element(By.CSS_SELECTOR, selector)
                                break
                            except NoSuchElementException:
                                continue

                        if not data_cell:
                            continue

                        duration_str = self._get_element_text(data_cell)
                        self.logger.info(f"Found Option Adjusted Duration: {duration_str}")

                        section_html = section.get_attribute('outerHTML')

                        return {
                            'product': product_key,
                            'date_str': date_str,
                            'duration_str': duration_str,
                            'raw_html': section_html
                        }

                except (NoSuchElementException, StaleElementReferenceException):
                    continue

        except Exception as e:
            self.logger.warning(f"Selenium extraction error: {e}")

        return None

    def _extract_via_beautifulsoup(self, product_key):
        """
        Fallback: parse the full page source with BeautifulSoup.
        This works even when Selenium .text returns empty due to overlays or rendering issues.
        """
        try:
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')

            # Find all fund characteristic sections
            sections = soup.find_all('div', class_='keyvalue')

            for section in sections:
                title = section.find(['h2', 'h3'], class_='comp-title')
                if not title or 'Fund Characteristics' not in title.get_text():
                    continue

                # Extract date
                date_str = None
                date_span = title.find('span', class_='date')
                if date_span:
                    date_str = date_span.get_text(strip=True)
                    if date_str.lower().startswith('as of '):
                        date_str = date_str[6:].strip()
                    self.logger.info(f"[BS4] Found date: {date_str}")

                # Extract Option Adjusted Duration from table
                table = section.find('table', class_='tb-keyvalue')
                if not table:
                    continue

                target_label = config.SELECTORS['option_adjusted_duration_label']

                for row in table.find_all('tr'):
                    label_cell = row.find(['th', 'td'], class_='label')
                    if not label_cell:
                        continue

                    label_text = label_cell.get_text(strip=True)
                    if target_label not in label_text:
                        continue

                    data_cell = row.find('td', class_='data')
                    if not data_cell:
                        continue

                    duration_str = data_cell.get_text(strip=True)
                    self.logger.info(f"[BS4] Found Option Adjusted Duration: {duration_str}")

                    section_html = str(section)

                    return {
                        'product': product_key,
                        'date_str': date_str,
                        'duration_str': duration_str,
                        'raw_html': section_html
                    }

        except Exception as e:
            self.logger.warning(f"BeautifulSoup extraction error: {e}")

        return None

    def scrape_product(self, product_key, url):
        """
        Scrape data for a single product with retry support.
        """

        self.logger.info(f"\n{'='*70}")
        self.logger.info(f"Scraping {product_key}: {url}")
        self.logger.info(f"{'='*70}")

        for attempt in range(1, config.MAX_RETRIES + 1):
            try:
                if attempt > 1:
                    self.logger.info(f"Retry attempt {attempt}/{config.MAX_RETRIES} for {product_key}")
                    time.sleep(config.RETRY_DELAY)

                # Navigate to page (also handles cookie modal)
                if not self.navigate_to_page(url):
                    self.logger.error(f"Failed to load page for {product_key}")
                    continue

                # Scroll to Fund Characteristics section
                if not self.scroll_to_fund_characteristics():
                    self.logger.warning(f"Could not scroll to Fund Characteristics for {product_key}")

                # Extract data
                data = self.extract_fund_data(product_key)

                if data:
                    self.logger.info(f"Successfully scraped {product_key}")
                    return data
                else:
                    self.logger.warning(f"Extraction returned no data for {product_key} (attempt {attempt})")

            except Exception as e:
                self.logger.error(f"Error scraping {product_key} (attempt {attempt}): {e}")

        self.logger.error(f"Failed to extract data for {product_key} after {config.MAX_RETRIES} attempts")
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
