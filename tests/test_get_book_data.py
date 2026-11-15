from unittest.mock import patch

from requests.exceptions import HTTPError

from scrapper import get_book_data

BOOK_URL = "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"


def test_get_book_data_parses_full_page(http_response, book_page_html):
    response = http_response(book_page_html)
    with patch(
        "scrapper.get_book_data.requests_get",
        return_value=response,
    ) as requests_get:
        book = get_book_data(BOOK_URL)

    requests_get.assert_called_once_with(BOOK_URL, timeout=15)
    assert book == {
        "url": BOOK_URL,
        "title": "A Light in the Attic",
        "price": "£51.77",
        "rating": 3,
        "rating_text": "Three",
        "availability": "In stock (22 available)",
        "quantity": 22,
        "description": "A delightful collection of poems.",
        "product_information": {
            "UPC": "a897fe39b1053632",
            "Product Type": "Books",
        },
    }


def test_get_book_data_fills_defaults_when_optional_fields_are_missing(
    http_response, sparse_book_page_html
):
    with patch(
        "scrapper.get_book_data.requests_get",
        return_value=http_response(sparse_book_page_html),
    ):
        book = get_book_data(BOOK_URL)

    assert book == {
        "url": BOOK_URL,
        "title": "",
        "price": "",
        "rating": 0,
        "rating_text": "Zero",
        "availability": "",
        "quantity": 0,
        "description": "",
        "product_information": {},
    }


def test_get_book_data_returns_none_on_http_error(http_response):
    response = http_response(status_code=500)
    error = HTTPError("server error")
    error.response = response
    response.raise_for_status.side_effect = error

    with patch("scrapper.get_book_data.requests_get", return_value=response):
        assert get_book_data(BOOK_URL) is None
