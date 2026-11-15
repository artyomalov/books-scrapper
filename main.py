from scrapper import START_URL, scrape_books

if __name__ == "__main__":
    scrape_books(
        is_save=True,
        max_pages=1,
        output_path="artifacts/books_data.txt",
        append=False,
        start_url=START_URL,
    )
