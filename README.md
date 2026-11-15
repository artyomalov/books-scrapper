# Парсер книг (books.toscrape.com)

Учебный проект собирает каталог сайта [books.toscrape.com](https://books.toscrape.com/): обходит страницы каталога, парсит карточку каждой книги и сохраняет результат в JSONL.

## Точка входа

**Точка входа — `main.py`.** Запуск из корня репозитория:

```bash
python main.py
```

Скрипт вызывает `scrape_books` для **одной** страницы каталога и перезаписывает файл `artifacts/books_data.txt` (режим `append=False`).

Пакет `scrapper` можно импортировать и из своего кода:

```python
from scrapper import scrape_books, get_book_data, START_URL

book = get_book_data(
    "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
)

scrape_books(max_pages=1, output_path="artifacts/books_data.txt", append=False)
```

`get_book_data` возвращает словарь (название, цена, рейтинг, наличие, описание, таблица Product Information) или `None`, если страницу не удалось загрузить или разобрать. `scrape_books` пишет каждую успешно обработанную книгу отдельной JSON-строкой и возвращает число таких книг. Ошибки HTTP/сети на страницах каталога пробрасываются; ошибка по одной книге логируется, книга пропускается.

Команды нужно выполнять из корня репозитория, чтобы импорт `scrapper` и запуск `main.py` находили пакет.

## Установка

Зависимости приложения:

```bash
pip install -r requirements.txt
```

Зависимости для тестов:

```bash
pip install -r requirements-dev.txt
```

Используемые библиотеки: `requests`, `beautifulsoup4`; для тестов достаточно `pytest` (мок HTTP — стандартный `unittest.mock`).

## Тесты

HTTP не вызывается: все сетевые вызовы замоканы.

```bash
pytest -v
```

## Структура

```
books_scrapper/
├── README.md
├── pytest.ini
├── requirements.txt          # requests, beautifulsoup4
├── requirements-dev.txt      # pytest
├── main.py                   # точка входа: scrape_books на одну страницу каталога
├── artifacts/
│   └── books_data.txt        # результат в формате JSONL
├── notebooks/
│   └── HW_03_python_ds_2026.ipynb
├── scrapper/
│   ├── __init__.py           # scrape_books, get_book_data, START_URL
│   ├── const.py              # BASE_URL, START_URL, RATING_MAP
│   ├── get_book_data.py      # разбор одной страницы книги
│   └── scrapper.py           # обход каталога
└── tests/
    ├── conftest.py
    ├── test_imports.py
    ├── test_get_book_data.py
    └── test_scrapper.py
```
