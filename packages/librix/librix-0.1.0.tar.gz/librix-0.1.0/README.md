# 📜 Librix

> A professional Python API and CLI for searching and retrieving metadata from Anna's Archive.

[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- 🔍 **Universal Search**: Search by query, language, format, and sorting.
- 🖼️ **Rich Metadata**: Extract titles, authors, publishers, and high-quality cover images.
- 🚀 **FastAPI Powered**: Modern, high-performance web interface.
- 🔗 **Mirror Links**: Dynamic extraction of fast and external download links.
- 💻 **CLI Interface**: Start the API server with a single command.

## Installation

```bash
pip install librix
```

## Usage

### As a Library

```python
from librix.scraper import AnnasArchiveScraper

scraper = AnnasArchiveScraper()
results = scraper.search("The Great Gatsby", lang="en", ext="epub")

for book in results:
    print(f"{book['title']} by {book['author']}")
    # Get details (mirrors, large cover)
    details = scraper.get_detail(book['md5'])
    print(details['mirrors'])
```

### As an API

Start the server:

```bash
librix
```

The API will be available at `http://localhost:8000`.

### Endpoints

- `GET /search?q={query}`: Search for books.
- `GET /detail/{md5}`: Get download mirrors and cover image.

## Disclaimer

This project is for educational purposes only. Please respect the terms of service of any website you interact with.

## License

MIT © [Kosma Gąsiorowski](mailto:kosma@example.com)
