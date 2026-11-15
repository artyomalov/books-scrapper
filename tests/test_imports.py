from importlib import import_module

from scrapper import START_URL, get_book_data, scrape_books


def test_package_exports_public_api():
    assert callable(scrape_books)
    assert callable(get_book_data)
    assert START_URL.startswith("https://books.toscrape.com/")


def test_package_modules_import():
    for module_name in (
        "scrapper",
        "scrapper.const",
        "scrapper.get_book_data",
        "scrapper.scrapper",
        "main",
    ):
        module = import_module(module_name)
        assert module is not None
