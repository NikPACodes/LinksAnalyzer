FROM python:3.12-slim

# Запрещаем Python создавать .pyc файлы (__pycache__).
ENV PYTHONDONTWRITEBYTECODE=1
# Отключае буферизацию stdout/stderr.
ENV PYTHONUNBUFFERED=1
# Запрещает pip сохранять скачанные пакеты в локальный cache.
# Аналог `pip install --no-cache-dir .`
ENV PIP_NO_CACHE_DIR=1

WORKDIR /app

# build-essential: Набор build tools для сборки C/C++-расширений (lxml, aiohttp, asyncpg).
# libxml2-dev:     Набор заголовков libxml2 для сборки lxml и обработки XML/HTML.
# libxslt1-dev:    Набор заголовков libxslt для сборки XSLT-поддержки в lxml.
# zlib1g-dev:      Набор заголовков zlib для поддержки сжатия при сборке lxml.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libxml2-dev \
        libxslt1-dev \
        zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY . .

RUN python -m pip install --upgrade pip \
    && python -m pip install ".[dev]"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]