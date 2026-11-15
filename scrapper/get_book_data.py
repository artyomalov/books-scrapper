from re import search
from typing import Any
from logging import getLogger

from bs4 import BeautifulSoup
from requests import get as requests_get
from requests.exceptions import (
    ConnectionError as RequestsConnectionError,
    HTTPError,
    RequestException,
    Timeout,
)

from .const import RATING_MAP

logger = getLogger(__name__)


def get_book_data(book_url: str) -> dict[str, Any] | None:
    """
    Получает информацию о книге с указанной страницы.

    Функция состоит из двух этапов — сетевого запроса и разбора
    HTML.  Все ожидаемые ошибки этих этапов перехватываются,
    логируются и приводят к возврату ``None``.  Неожидаемые
    исключения логируются через ``logger.exception`` и
    пробрасываются наружу, чтобы не скрывать баги.

    Parameters
    ----------
    book_url : str
        Абсолютный URL страницы книги на books.toscrape.com.

    Returns
    -------
    dict[str, Any] | None
        Словарь с данными о книге при успехе. Ключи:

        - ``"url"`` (str) — исходный URL книги;
        - ``"title"`` (str) — название (пустая строка, если не найдено);
        - ``"price"`` (str) — цена как в HTML, например ``"£51.77"``;
        - ``"rating"`` (int) — числовой рейтинг (0–5) по ``RATING_MAP``;
        - ``"rating_text"`` (str) — словесный рейтинг (``"One"``…
          ``"Five"``), ``"Zero"`` если не найден;
        - ``"availability"`` (str) — текст блока наличия;
        - ``"quantity"`` (int) — число доступных экземпляров
          (0, если не удалось распарсить);
        - ``"description"`` (str) — описание (пустая строка, если
          отсутствует);
        - ``"product_information"`` (dict[str, str]) — таблица
          Product Information (пустой словарь, если таблицы нет).

        ``None`` возвращается, если страницу не удалось получить
        или разобрать:

        - сетевые ошибки запроса: таймаут, обрыв соединения,
          SSL/прокси-ошибки и прочие ``RequestException``;
        - HTTP-ошибки ``4xx``/``5xx``;
        - некорректная или нестандартная структура HTML: отсутствует
          ``div.product_main``, ожидаемые теги имеют неожидаемый тип
          (``ValueError``, ``AttributeError``, ``IndexError``,
          ``KeyError``).

    Raises
    ------
    Exception
        Любое исключение, не относящееся к перечисленным выше
        ожидаемым категориям, логируется и пробрасывается
        вызывающему коду — чтобы не маскировать реальные
        программные ошибки.

    Notes
    -----
    Таймаут сетевого запроса зафиксирован на 15 секундах.
    """
    logger.info("Get data from url %s", book_url)

    # Запрос к ресурсу
    try:
        response = requests_get(book_url, timeout=15)
        response.raise_for_status()
    except HTTPError as error:
        status = getattr(error.response, "status_code", "unknown")
        logger.error(
            "HTTP error while fetching %s (status=%s): %s",
            book_url,
            status,
            error,
        )
        return None
    except Timeout:
        logger.error("Timeout while fetching %s (timeout=15s)", book_url)
        return None
    except RequestsConnectionError as error:
        logger.error("Connection error while fetching %s: %s", book_url, error)
        return None
    except RequestException as error:
        # catch-all for other requests failures (SSL, proxy, too many redirects, …)
        logger.error("Request error while fetching %s: %s", book_url, error)
        return None

    # Парсинг
    try:
        soup = BeautifulSoup(response.text, "html.parser")

        product_main = soup.find("div", class_="product_main")
        if product_main is None:
            raise ValueError(f"Не найден блок product_main: {book_url}")

        title_tag = product_main.find("h1")
        price_tag = product_main.find("p", class_="price_color")
        rating_tag = product_main.find("p", class_="star-rating")
        availability_tag = product_main.find("p", class_="instock availability")

        title = title_tag.get_text(strip=True) if title_tag else ""
        price = price_tag.get_text(strip=True) if price_tag else ""

        rating_classes = rating_tag.get("class", []) if rating_tag else []
        rating_word = rating_classes[-1] if rating_classes else "Zero"
        rating = RATING_MAP.get(rating_word, 0)

        availability = (
            availability_tag.get_text(" ", strip=True) if availability_tag else ""
        )

        quantity_match = search(r"\((\d+)\s+available\)", availability)
        quantity = int(quantity_match.group(1)) if quantity_match else 0

        description = ""
        description_tag = soup.find("div", id="product_description")
        if description_tag:
            description_paragraph = description_tag.find_next_sibling("p")
            if description_paragraph:
                description = description_paragraph.get_text(" ", strip=True)

        product_information: dict[str, str] = {}
        table = soup.find("table", class_="table-striped")
        if table:
            for row in table.find_all("tr"):
                th = row.find("th")
                td = row.find("td")
                if th and td:
                    product_information[th.get_text(strip=True)] = td.get_text(
                        " ", strip=True
                    )

        return {
            "url": book_url,
            "title": title,
            "price": price,
            "rating": rating,
            "rating_text": rating_word,
            "availability": availability,
            "quantity": quantity,
            "description": description,
            "product_information": product_information,
        }

    except (ValueError, AttributeError, IndexError, KeyError) as error:
        # Страница имеет нестандартную структуру
        logger.error("Failed to parse book page %s: %s", book_url, error)
        return None
    except Exception:
        # Обработка неожидаемых исключений. Выбрасываем исключение,
        # так как логичнее делегировать обработку таких ошибок вызывающей
        # функции
        logger.exception("Unexpected error while processing %s", book_url)
        raise
