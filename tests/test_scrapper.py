import json
from unittest.mock import patch

from pytest import raises
from requests.exceptions import HTTPError

from scrapper import scrape_books

START_URL = "https://books.toscrape.com/catalogue/page-1.html"
BOOK_URL = "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"


def test_scrape_books_writes_parsed_book(http_response, catalog_page_html, tmp_path):
    book = {"url": BOOK_URL, "title": "A Light in the Attic"}
    output = tmp_path / "books_data.txt"

    with (
        patch(
            "scrapper.scrapper.get",
            return_value=http_response(catalog_page_html),
        ),
        patch("scrapper.scrapper.get_book_data", return_value=book) as get_book_data,
    ):
        count = scrape_books(
            start_url=START_URL, output_path=output, max_pages=1, append=False
        )

    get_book_data.assert_called_once_with(BOOK_URL)
    assert count == 1
    assert json.loads(output.read_text(encoding="utf-8")) == book


def test_scrape_books_does_not_request_pages_past_max_pages(
    http_response, catalog_page_html, tmp_path
):
    first_page = http_response(catalog_page_html)
    second_page = http_response("<html><body></body></html>")

    with (
        patch(
            "scrapper.scrapper.get",
            side_effect=[first_page, second_page],
        ) as catalog_get,
        patch(
            "scrapper.scrapper.get_book_data",
            return_value={"title": "A Light in the Attic"},
        ),
    ):
        scrape_books(
            start_url=START_URL,
            output_path=tmp_path / "books_data.txt",
            max_pages=1,
            append=False,
        )

    catalog_get.assert_called_once_with(START_URL, timeout=15)


def test_scrape_books_raises_when_first_catalog_page_returns_404(
    http_response, tmp_path
):
    response = http_response(status_code=404)
    error = HTTPError("not found")
    error.response = response
    response.raise_for_status.side_effect = error

    with (
        patch("scrapper.scrapper.get", return_value=response),
        raises(HTTPError),
    ):
        scrape_books(start_url=START_URL, output_path=tmp_path / "books_data.txt")
