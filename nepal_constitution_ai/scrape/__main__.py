from nepal_constitution_ai.scrape.scrape import main as scrape_main
from nepal_constitution_ai.scrape.download_pdfs import main as download_main
from nepal_constitution_ai.scrape.organize_folders import main as organize_main

if __name__ == "__main__":
    print("Starting the documents info scraping process...")
    scrape_main()  # Run the scraping script
    print("Scraping completed.\n")

    print("Starting the document download process...")
    download_main()  # Run the downloading script
    print("Download completed.\n")

    print("Starting the downloaded document files organization process...")
    organize_main()  # Run the organization script
    print("File organization completed.\n")

    print("All tasks completed successfully!")
