import asyncio
from concurrent.futures import ThreadPoolExecutor

from bs4 import BeautifulSoup

from app.analyzer.dto import FetchResult, HtmlParseResult


class HtmlParser:
    """
    Парсер HTML-страниц.

    Выполняет синхронный разбор HTML через BeautifulSoup/lxml,
    но запускает эту работу в отдельном ThreadPoolExecutor,
    чтобы не блокировать asyncio event loop.
    """
    def __init__(self, max_workers: int, max_title_length: int, max_description_length: int):
        self.max_workers = max_workers
        self.max_title_length = max_title_length
        self.max_description_length = max_description_length
        self._executor = ThreadPoolExecutor(max_workers=max_workers)


    @staticmethod
    def _normalize_text(value: str) -> str:
        """
        Нормализация текста.
        """
        return " ".join(value.strip().split())


    def _extract_title(self, soup: BeautifulSoup) -> str | None:
        """
        Извлечение и нормализация title.

        ! Если title превышает максимальный размер,
        то обрезаем до max_title_length символов.
        """
        if soup.title is None:
            return None

        if soup.title.string is None:
            return None

        # Нормализация
        title = self._normalize_text(soup.title.string)

        if not title:
            return None

        return title[:self.max_title_length]


    def _extract_description(self, soup: BeautifulSoup) -> str | None:
        """
        Извлекает и нормализация meta description.

        ! Если description превышает максимальный размер,
        то обрезаем до max_description_length символов.
        """
        # Ищем по стандартному тегу
        meta_description = soup.find('meta', attrs={'name': 'description'})

        # Ищем по Open Graph описанию
        # (как доп.источник при отсутствии стандартного)
        if meta_description is None:
            meta_description = soup.find('meta', attrs={'property': 'og:description'})

        if meta_description is None:
            return None

        content = meta_description.get('content')

        if not content:
            return None

        # Нормализация
        description = self._normalize_text(str(content))

        if not description:
            return None

        return description[:self.max_description_length]


    def _parse_sync(self, html: str) -> HtmlParseResult:
        """
        Парсинг HTML и извлечение основных метаданных.

        BeautifulSoup работает в синхронном режиме,
        поэтому запускаем метод выполняется ThreadPoolExecutor.
        """
        # Создание BeautifulSoup для удобного поиска и извлечения данных из HTML.
        soup = BeautifulSoup(html, 'lxml')

        # Извлечение title из HTML
        title = self._extract_title(soup)
        # Извлечение description из HTML
        description = self._extract_description(soup)

        # Подсчет кол-ва ссылок
        links_count = len(soup.find_all("a", href=True))
        # Подсчет кол-ва картинок
        images_count = len(soup.find_all("img", src=True))

        return HtmlParseResult(title=title, description=description,
                               links_count=links_count, images_count=images_count)


    async def parse(self, fetch_result: FetchResult) -> HtmlParseResult | None:
        """
        Асинхронная обертка для запуска парсинга HTML в отдельном потоке.

        Чтобы синхронная работа BeautifulSoup не блокировала event loop,
        запускаем парсинг в отдельном потоке.
        """
        if fetch_result.error is not None:
            return None

        if not fetch_result.html:
            return None

        loop = asyncio.get_running_loop()

        # Запуск парсинга в отдельном потоке, чтобы не блокировать event loop
        return await loop.run_in_executor(self._executor,
                                          self._parse_sync,
                                          fetch_result.html)


    def shutdown(self) -> None:
        """
        Завершение работы ThreadPoolExecutor.
        """
        self._executor.shutdown(wait=True)