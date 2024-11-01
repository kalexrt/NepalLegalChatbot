import re
import requests

def download_pdf(pdf_url, output_dir, title):
    try:
        pdf_data = requests.get(pdf_url)
        pdf_data.raise_for_status()  # Ensure the request was successful
        
        # Save the PDF
        try:
            pdf_filename = output_dir + '/' + clean_filename(title)
            with open(pdf_filename, "wb") as f:
                f.write(pdf_data.content)
        except OSError as exc:
            if exc.errno == 36:
                pdf_filename = output_dir + '/filename_shortened_' + clean_filename(title)[:10] + '.pdf'
                with open(pdf_filename, "wb") as f:
                    f.write(pdf_data.content)

        print(f"Downloaded '{pdf_filename}' successfully.\n")
        
    except requests.exceptions.RequestException as e:
        print(f"Failed to download PDF from {pdf_url}: {e}\n")     


def extract_last_pdf_url(text):
    # Regular expression to find all URLs that start with 'https' and end with '.pdf'
    pattern = r'https://[^\s]+\.pdf'
    urls = re.findall(pattern, text)  # Find all matching URLs

    # Return the last URL if any found, otherwise None
    return urls[-1] if urls else None


def clean_filename(title):
    """Clean the title to make it a valid filename"""
    # Remove invalid filename characters
    cleaned = re.sub(r'[<>:"/\\|?*]', '', title)
    # Remove extra whitespace
    cleaned = '_'.join(cleaned.split())
    # Limit filename length
    cleaned = cleaned[:100]
    return cleaned + '.pdf'
