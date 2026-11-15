"""Парсер книг с сайта books.toscrape.com."""

from requests import get
from json import dumps
from logging import getLogger
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from requests.exceptions import HTTPError, RequestException

from .const import START_URL
from .get_book_data import get_book_data

logger = getLogger(__name__)


def scrape_books(
    start_url: str = START_URL,
    is_save: bool = True,
    append: bool = True,
    max_pages: int | None = None,
    output_path: str | Path = "../artifacts/books_data.txt",
) -> int:
    """
    Собирает данные со всех страниц каталога books.toscrape.com
    и пишет их в файл построчно (JSONL), не накапливая
    в памяти.

    Файл открывается в режиме ``"a"`` (append), поэтому
    создаётся автоматически, если его не существует. При
    ``append=False`` файл перезаписывается. Родительские
    папки создаются автоматически.

    Ошибки на уровне отдельной книги (недоступная страница,
    некорректный HTML, отсутствующие поля) не прерывают обход:
    книга пропускается с записью в лог, обработка продолжается
    со следующей. 404 на страницах каталога, начиная со второй,
    трактуется как конец каталога.

    Parameters
    ----------
    start_url : str, default=START_URL
        URL первой страницы каталога.
    is_save : bool, default=True
        Если True — книги пишутся в ``output_path``.
        Если False — данные не сохраняются, но обход и подсчёт
        книг выполняются (полезно для «сухого прогона» /
        проверки доступности).
    append : bool, default=True
        True — дописывать в конец файла (``"a"``),
        False — перезаписывать (``"w"``).
    max_pages : int | None, default=None
        Максимальное количество страниц каталога, которые нужно
        обойти (имеются в виду именно страницы каталога, а не
        книги). ``None`` — без ограничения. Например,
        ``max_pages=1`` обработает только первую страницу
        каталога.
    output_path : str | Path, default="books_data.txt"
        Путь к файлу. Родительские папки создаются
        автоматически.

    Returns
    -------
    int
        Количество успешно обработанных книг (независимо от
        значения ``is_save``).

    Raises
    ------
    HTTPError
        Не-404 ошибка при загрузке страницы каталога, либо 404
        на первой странице каталога (``page_number == 1``).
    RequestException
        Сетевые ошибки при загрузке страницы каталога:
        таймаут, обрыв соединения и т.п.

    Notes
    -----
    Ошибки загрузки/разбора страницы отдельной книги (в том
    числе непойманные исключения из :func:`get_book_data`)
    не пробрасываются наружу — они логируются как warning,
    а соответствующая книга пропускается и не увеличивает
    возвращаемый счётчик.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if append else "w"

    count = 0
    page_url: str | None = start_url
    page_number = 1

    # Файл открываем один раз; open("a") сам создаст его, если нет.
    with output_file.open(mode, encoding="utf-8") as file:
        while page_url:
            # Если номер страницы больше, чем максимальное число страниц
            # прерываем выполнение цикла
            if max_pages is not None and page_number > max_pages:
                break

            try:
                logger.info("Запрос к странице: %s", page_url)

                response = get(page_url, timeout=15)
                response.raise_for_status()
            except HTTPError as error:
                status = (
                    error.response.status_code if error.response is not None else None
                )

                if status == 404 and page_number > 1:
                    logger.info("Достигнут конец каталога (404): %s", page_url)
                    break

                if status == 404:
                    logger.error(
                        "Стартовая страница каталога недоступна (404): %s",
                        page_url,
                    )
                    raise

                logger.error(
                    "Ошибка загрузки каталога %s (status=%s): %s",
                    page_url,
                    status,
                    error,
                )
                raise
            except RequestException as error:
                logger.error("Сетевая ошибка на %s: %s", page_url, error)
                raise

            soup = BeautifulSoup(response.text, "html.parser")

            for article in soup.select("article.product_pod"):
                link = article.select_one("h3 a")
                if link is None or not link.get("href"):
                    continue

                book_url = urljoin(page_url, link["href"])
                try:
                    book = get_book_data(book_url)
                    if book is None:
                        logger.warning(
                            "Не удалось получить данные для книги по адресу, %s",
                            book_url,
                        )
                        continue
                except Exception as error:
                    logger.warning("Пропущена книга %s: ; Причина: %s", book_url, error)
                    continue

                if is_save:
                    file.write(dumps(book, ensure_ascii=False) + "\n")
                count += 1

            next_link = soup.select_one("li.next a")
            page_url = urljoin(page_url, next_link["href"]) if next_link else None

            if page_url is None:
                # Если страницы закончились прерываем цикл
                break

            page_number += 1

    if is_save:
        logger.info(
            "Данные сохранены: %s (всего книг: %d)",
            output_file.resolve(),
            count,
        )
    else:
        logger.info("Обработано адресов: %d", count)

    return count
