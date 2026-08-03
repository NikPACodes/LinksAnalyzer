from pydantic import BaseModel, ConfigDict


class FetchResult(BaseModel):
    """
    Результат загрузки URL.
    """
    model_config = ConfigDict(frozen=True)

    url: str                     # Для aiohttp удобнее использовать str вместо HttpUrl
    status_code: int | None
    response_time_ms: int | None
    html: str | None
    html_size_bytes: int
    error: str | None


class HtmlParseResult(BaseModel):
    """
    Результат парсинга HTML-страницы.
    """
    model_config = ConfigDict(frozen=True)

    title: str | None
    description: str | None
    links_count: int
    images_count: int