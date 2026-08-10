import time
from uuid import UUID

from pydantic import HttpUrl
from sqlalchemy.ext.asyncio import AsyncSession

from app.analyzer.cache import AnalysisCache
from app.analyzer.dto import CachedAnalysisResult, FetchResult, HtmlParseResult
from app.analyzer.fetcher import WebsiteFetcher
from app.analyzer.models import AnalysisTask
from app.analyzer.parser import HtmlParser
from app.analyzer.repositories.result_repository import WebsiteResultRepository
from app.analyzer.repositories.task_repository import AnalysisTaskStatus, TaskRepository
from app.core.config import get_settings
from app.core.redis import get_redis_cache_client


class AnalyzerService:
    """
    Сервисный слой анализа.
    Service объединяет несколько repository-операций в один бизнес-сценарий.
    """
    def __init__(self, db: AsyncSession):
        """
        Инициализировать сервис анализа.

        Внутри сервиса создаются repository-объекты AnalysisTask и WebsiteResult,
        для используют единой db-сессии и создания в рамках одной транзакции.
        """
        self.db = db
        self.settings = get_settings()
        self.task_repository = TaskRepository(db)
        self.result_repository = WebsiteResultRepository(db)


    @staticmethod
    def _normalize_urls(urls: list[HttpUrl]) -> list[str]:
        """
        Нормализация перечня URL.

        - Преобразуем каждый HttpUrl в str.
        - избавляемся от URL дубликатов.
        - сохраняем исходный порядок URL.
        """
        # dict.fromkeys использован для сохранения порядка URL
        return list(dict.fromkeys(str(url) for url in urls))


    @staticmethod
    def _should_cache_result(*, fetch_result: FetchResult, parse_result: HtmlParseResult | None) -> bool:
        """
        Проверка условий для кэширования
        """
        if (fetch_result.error is None and fetch_result.status_code is not None
            and parse_result is not None and 200 <= fetch_result.status_code < 400):
            return True
        else:
            return False


    @staticmethod
    def _build_cached_result(*, fetch_result: FetchResult,
                                parse_result: HtmlParseResult | None) -> CachedAnalysisResult:
        """
        Подготовка результатов для кэширования
        """
        if parse_result is None:
            raise ValueError('parse_result отсутствует')
        return CachedAnalysisResult(url=fetch_result.url, status_code=fetch_result.status_code,
                                    response_time_ms=fetch_result.response_time_ms,
                                    title=parse_result.title, description=parse_result.description,
                                    links_count=parse_result.links_count, images_count=parse_result.images_count,
                                    html_size_bytes=fetch_result.html_size_bytes, error=fetch_result.error)


    async def create_task(self, urls:list[HttpUrl]) -> AnalysisTask:
        """
        Создание новой задачи для анализа сайтов.

        !!! Commit выполняется только после корректного создания всех записей AnalysisTask и WebsiteResult.
        !!! В случае возникновения ошибки производит rollback.
        """
        # Нормализуем URLs
        normalized_urls = self._normalize_urls(urls)

        try:
            # Создаем новую задачу
            task = await self.task_repository.create_task(total_urls=len(normalized_urls))
            # Создаем предварительных перечень результатов анализа
            await self.result_repository.create_pending_results(task_id=task.id, urls=normalized_urls)

            # Выполняем коммит только в случае выполнения всех repository-операций
            await self.db.commit()
            await self.db.refresh(task)

            return task

        except Exception:
            # Откатываем изменения при возникновении ошибки
            await self.db.rollback()
            raise


    async def fetch_task_urls(self, task_id: UUID, *, use_cache: bool = True) -> AnalysisTask | None:
        """
        Выполнение асинхронной загрузки всех URL, связанных с задачей,
        и выполняем парсинг полученных HTML-страниц.
        """
        task = await self.task_repository.get_task(task_id=task_id)

        if task is None:
            return None

        # Страховка от двойного запуска
        if task.status in {AnalysisTaskStatus.PROCESSING, AnalysisTaskStatus.DONE}:
            return task

        # Получение перечня URLs по задаче
        urls = await self.result_repository.get_urls(task_id)

        # Создаем aiohttp загрузчик
        fetcher = WebsiteFetcher(timeout_seconds=self.settings.fetch_timeout_seconds,
                                 concurrency=self.settings.fetch_concurrency,
                                 max_response_size_bytes=self.settings.fetch_max_response_size_bytes,
                                 user_agent=self.settings.fetch_user_agent)

        # Создаем HTML парсер
        parser = HtmlParser(max_workers=self.settings.html_parser_max_workers,
                            max_title_length=self.settings.html_parser_max_title_length,
                            max_description_length=self.settings.html_parser_max_description_length)

        # Работа кэшем результатов
        cache = AnalysisCache(client=get_redis_cache_client(self.settings),
                              ttl_seconds=self.settings.analysis_cache_ttl_seconds,
                              key_prefix=self.settings.analysis_cache_key_prefix)

        try:
            await self.task_repository.set_status(task, status=AnalysisTaskStatus.PROCESSING)
            # Commit делается сразу, для отображения, что задача обрабатывается.
            await self.db.commit()
            commit_at = time.monotonic()

            # # Асинхронная загрузка URLs.
            # fetch_results = await fetcher.fetch_many(urls)

            processed_urls = 0

            # for fetch_result in fetch_results:
            #     await self.result_repository.update_fetch_result(task_id=task.id, fetch_result=fetch_result)
            #     processed_urls += 1
            #     await self.task_repository.set_processed_urls(task, processed_urls=processed_urls)

            commit_every = 5              # Интервал обработанных URL
            commit_interval_seconds = 2   # Интервал времени между коммитами
            urls_to_fetch: list[str] = []  # Перечень URL для обработки

            # -------------------------------------------------------------------
            # Проверяем кэш и получаем результаты анализа URLs из кэша
            # -------------------------------------------------------------------
            for url in urls:
                if not use_cache:
                    urls_to_fetch.append(url)
                    continue

                cached_result = await cache.get(url)

                if cached_result is None:
                    # Добавляем URL в перечень на обработку
                    urls_to_fetch.append(url)
                    continue

                await self.result_repository.update_from_cache(task_id=task.id, cached_result=cached_result)

                processed_urls += 1
                await self.task_repository.set_processed_urls(task=task, processed_urls=processed_urls)

                now = time.monotonic()
                interval = now - commit_at

                # Делаем commit только при условии достижения commit_every, либо commit_interval_seconds
                if processed_urls % commit_every == 0 or interval >= commit_interval_seconds:
                    await self.db.commit()
                    commit_at = now
            # -------------------------------------------------------------------


            # -------------------------------------------------------------------
            # Загрузка и парсинг URLs
            # -------------------------------------------------------------------
            # Для получения live-progress используем метод fetcher.fetch_many_iter,
            # т.к. он позволяет не дожидаться загрузки всех URLs и позволяет обновлять результаты по готовности.
            # ! Данный подход создает live-progress, но значительно повышает нагрузку на БД из-за коммитов.
            # Для уменьшения нагрузки на БД коммиты делаются с интерваломи (commit_interval_seconds),
            # либо по достижению N результатов (commit_every).
            async for fetch_result in fetcher.fetch_many_iter(urls_to_fetch):
                # Запускаем парсинг
                # TODO переделать на настоящую многопоточность (pipeline)
                # Парсинг запускается в отдельном потоке чтобы не блокировать event loop,
                # но из-за await ожидает завершения -> получаем лишь 1 активую parse-задачу внутри цикла
                parse_result = await parser.parse(fetch_result)

                await self.result_repository.update_fetch_result(task_id=task.id,
                                                                 fetch_result=fetch_result,
                                                                 parse_result=parse_result)

                # Проверяем на необходимость кэширования
                if self._should_cache_result(fetch_result=fetch_result, parse_result=parse_result):
                    # Подготавливаем и кэшируем результат
                    await cache.set(self._build_cached_result(fetch_result=fetch_result, parse_result=parse_result))

                processed_urls += 1
                await self.task_repository.set_processed_urls(task, processed_urls=processed_urls)

                now = time.monotonic()
                interval = now - commit_at

                # Делаем commit только при условии достижения commit_every, либо commit_interval_seconds
                if processed_urls % commit_every == 0 or interval >= commit_interval_seconds:
                    await self.db.commit()
                    commit_at = now
            # -------------------------------------------------------------------

            await self.task_repository.set_status(task, status=AnalysisTaskStatus.DONE)
            # Фиксируем все изменения
            await self.db.commit()
            await self.db.refresh(task)

            return task

        except Exception as exc:
            await self.db.rollback()

            await self.task_repository.set_status(task, status=AnalysisTaskStatus.FAILED, error=f'{exc}')
            await self.db.commit()
            await self.db.refresh(task)

            return task

        finally:
            parser.shutdown()
            await cache.close()