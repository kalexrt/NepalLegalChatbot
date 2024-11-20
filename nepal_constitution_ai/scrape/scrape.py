from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import json
from nepal_constitution_ai.scrape.utils import clean_filename

DATA_PATH = "data"

# Base URL
BASE_URL = "https://lawcommission.gov.np"
START_URL = f"{BASE_URL}/pages/list-volume-act/"

# Additional URLs
URLS = [
    {"recent_acts": "/2163/"},
    {"constitution": "/1807/"},
    {"act_not_in_volume": "/2166/"},
    {"rules_and_regulations": "/1811/"},
    {"others": "/others/"},
]

def init_driver():
    """Initialize Selenium WebDriver in headless mode."""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver_path = "driver/chromedriver"  # Replace with your driver path
    return webdriver.Chrome(executable_path=driver_path, options=options)

def switch_language(driver, language):
    """Switch the website language."""
    if language not in ['en', 'ne']:
        raise ValueError("Invalid language code. Use 'en' for English or 'ne' for Nepali.")
    try:
        driver.execute_script(f"document.getElementById('language-select').value = '{language}';")
        driver.execute_script("document.getElementById('language-select').form.submit();")
        print(f"Switched to {'English' if language == 'en' else 'Nepali'}...")
        time.sleep(2)
    except Exception as e:
        print(f"Error switching language: {e}")

def fetch_page_source(driver, url):
    """Load page and return the source."""
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        return driver.page_source
    except Exception as e:
        print(f"Failed to load {url}: {e}")
        return None

def parse_volumes(page_content):
    """Parse volume links from the main page."""
    soup = BeautifulSoup(page_content, 'html.parser')
    volume_links = {}
    table_div = soup.find("div", class_="table-responsive custom-bs-table old__pmList")
    if table_div:
        for row in table_div.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) >= 2:
                volume_name = cells[1].text.strip()
                link_tag = cells[1].find("a", class_="in-cell-link")
                if link_tag and link_tag['href']:
                    volume_links[volume_name] = (
                        BASE_URL + link_tag['href'] if link_tag['href'].startswith("/") else link_tag['href']
                    )
    return volume_links

def parse_pdfs(page_source):
    """Extract PDF titles and links from a page."""
    soup = BeautifulSoup(page_source, 'html.parser')
    pdfs = []
    for row in soup.find_all('tr'):
        cells = row.find_all('td')
        if len(cells) >= 2:
            title = cells[1].text.strip() if len(cells) > 1 else "Unknown Title"
            link_tag = row.find('a', href=True)
            if link_tag and link_tag['href'].endswith('.pdf'):
                pdf_url = (
                    BASE_URL + link_tag['href'] if link_tag['href'].startswith("/") else link_tag['href']
                )
                pdfs.append((title, pdf_url))
    return pdfs

def parse_pdfs_with_pagination(base_url, driver):
    """Parse PDFs across paginated pages."""
    documents = []
    page = 1
    while True:
        paginated_url = f"{base_url}?page={page}"
        print(f"Fetching: {paginated_url}")
        driver.get(paginated_url)
        if "Error 404" in driver.title:
            break
        page_content = driver.page_source
        page_documents = parse_pdfs(page_content)
        if not page_documents:
            break
        documents.extend(page_documents)
        page += 1
        time.sleep(1)
    return documents

def process_url_category(driver, url, category_name):
    """Process a specific URL category."""
    results = []

    fetch_page_source(driver, START_URL)
    switch_language(driver, 'ne')  # Nepali titles
    pdfs_ne = parse_pdfs_with_pagination(url, driver)

    fetch_page_source(driver, START_URL)
    switch_language(driver, 'en')  # English titles
    pdfs_en = parse_pdfs_with_pagination(url, driver)

    for i in range(max(len(pdfs_ne), len(pdfs_en))):
        nepali = pdfs_ne[i] if i < len(pdfs_ne) else ("Unknown Title (Nepali)", "")
        english = pdfs_en[i] if i < len(pdfs_en) else ("Unknown Title (English)", "")
        results.append({
            "nep_title": nepali[0],
            "eng_title": english[0],
            "nep_pdf_link": nepali[1],
            "eng_pdf_link": english[1],
            "filename": clean_filename(nepali[0]),
        })
    return {category_name: results}

def save_to_json(data, filename="documents_info.json"):
    """Save data to JSON."""
    filename = f"{DATA_PATH}/{filename}"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"Saved results to {filename}")



def main():
    driver = init_driver()
    try:
        results = {"act_in_volume": {}}

        # Process volumes
        fetch_page_source(driver, START_URL)
        switch_language(driver, 'en')
        main_page_content = fetch_page_source(driver, START_URL)
        volumes = parse_volumes(main_page_content)
        print("Extracted the volume names")

        print(f"Processing category: act_in_volume")
        for volume_name, volume_url in volumes.items():
            print(f"Processing volume: {volume_name}")
            results["act_in_volume"][volume_name] = process_url_category(driver, volume_url, volume_name)

        # Process additional URLs
        for category in URLS:
            for name, path in category.items():
                print(f"Processing category: {name}")
                url = BASE_URL + "/category" + path
                results.update(process_url_category(driver, url, name))

        save_to_json(results)
    finally:
        driver.quit()
