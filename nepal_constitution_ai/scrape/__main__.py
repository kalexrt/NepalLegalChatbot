import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from nepal_constitution_ai.scrape.scrape import scrape_documents_info, find_pdf_link
from nepal_constitution_ai.scrape.utils import download_pdf
from nepal_constitution_ai.config.config import settings

# Set up Chrome options and enable logging for network requests
options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

# Set up Chrome capabilities for network logging
capabilities = DesiredCapabilities.CHROME
capabilities["goog:loggingPrefs"] = {"performance": "ALL"}  # Enable performance logging

# Path to ChromeDriver
chrome_service = Service('./driver/chromedriver')

# Initialize the WebDriver with network logging enabled
driver = webdriver.Chrome(service=chrome_service, options=options, desired_capabilities=capabilities)

def main():
    # Create output directory
    os.makedirs(settings.DOWNLOADED_PDF_PATH, exist_ok=True)
    
    total_pages = 66 # Number of pages to scrape from the https://lawcommission.gov.np/category/1806/?page={page_num}
    
    page_urls_data = []

    for page_num in range(1, total_pages + 1):
        print(f"\nProcessing page {page_num}/{total_pages}")
        page_urls_data += scrape_documents_info(page_num)
        time.sleep(1) # Sleep for 1 second to prevent getting blocked from server
    print("\n")

    # Loop through each page URL to capture the PDF link
    for url_data in page_urls_data:
        title, url = url_data
        pdf_url = find_pdf_link(driver, url)

        if not pdf_url:
            print("No PDF link found on this page.\n")
            continue

        print(f"Found PDF URL: {pdf_url}\n")
        download_pdf(pdf_url, settings.DOWNLOADED_PDF_PATH, title)


    # Close the browser
    driver.quit()
        
    print(f"\nDownload complete!")


if __name__ == "__main__":
    main()