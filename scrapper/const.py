from urllib.parse import urljoin

BASE_URL = "https://books.toscrape.com/"
RATING_MAP = {
    "One": 1,
    "Two": 2,
    "Three": 3,
    "Four": 4,
    "Five": 5,
}


START_URL = urljoin(BASE_URL, "catalogue/page-1.html")
