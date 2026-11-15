"""Shared fixtures. Network access is never used; tests mock HTTP clients."""

from pathlib import Path
from sys import path
from unittest.mock import Mock

from pytest import fixture

# Make `import scrapper` work even if pytest is started outside the repo root.
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in path:
    path.insert(0, str(_PROJECT_ROOT))


@fixture
def http_response():
    """Build a requests-like response whose body is supplied by the test."""

    def _build(text: str = "", status_code: int = 200):
        response = Mock()
        response.text = text
        response.status_code = status_code
        response.raise_for_status.return_value = None
        return response

    return _build


@fixture
def book_page_html() -> str:
    return """
    <html><body>
      <div class="product_main">
        <h1>A Light in the Attic</h1>
        <p class="price_color">£51.77</p>
        <p class="star-rating Three">Three</p>
        <p class="instock availability">In stock (22 available)</p>
      </div>
      <div id="product_description"></div>
      <p>A delightful collection of poems.</p>
      <table class="table-striped">
        <tr><th>UPC</th><td>a897fe39b1053632</td></tr>
        <tr><th>Product Type</th><td>Books</td></tr>
      </table>
    </body></html>
    """


@fixture
def sparse_book_page_html() -> str:
    """product_main is present, but every optional field is missing."""
    return """
    <html><body>
      <div class="product_main"></div>
    </body></html>
    """


@fixture
def catalog_page_html() -> str:
    return """
    <html><body>
      <article class="product_pod">
        <h3><a href="a-light-in-the-attic_1000/index.html">A Light in the Attic</a></h3>
      </article>
      <li class="next"><a href="page-2.html">next</a></li>
    </body></html>
    """
