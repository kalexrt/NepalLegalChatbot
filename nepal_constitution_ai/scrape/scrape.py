import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from nepal_constitution_ai.scrape.utils import extract_last_pdf_url

BASE_URL = "https://lawcommission.gov.np"

def scrape_documents_info(page_num):
    """Scrape all the link and title of the available documents on the given page num of the given url"""

    url = f"{BASE_URL}/category/1806/?page={page_num}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all document titles and their content links
        documents_info = []
        for title_elem in soup.find_all('h3', class_='card__title'):
            link = title_elem.find('a')
            if link:
                title = link.text.strip()
                content_url = urljoin(BASE_URL, link['href'])
                documents_info.append((title, content_url))
        
        return documents_info
            
    except Exception as e:
        print(f"Error scraping page {page_num}: {str(e)}")
        return 0


def find_pdf_link(driver, url):
    """Find the link to the document PDF from the given document url page"""

    print(f"Processing page: {url}\n")
    driver.get(url)
    
    # Wait a few seconds to allow network requests to complete
    time.sleep(5)
    
    # Retrieve network logs and find the PDF URL
    for entry in driver.get_log("performance"):
        log = entry["message"]
        if ".pdf" in log:  # Look for .pdf in the log
            # Extract URL from the log entry
            start_index = log.find("https://")
            end_index = log.find(".pdf") + 4
            pdf_url_raw = log[start_index:end_index]
            pdf_url = extract_last_pdf_url(pdf_url_raw)
            return pdf_url
    
    return None

 

