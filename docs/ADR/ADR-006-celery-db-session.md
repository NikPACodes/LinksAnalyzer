# ADR-006: Изоляция подключения к БД для Celery Worker

---


## Причина

FastAPI и Celery работают в разных `runtime contexts` и имеют независимый lifecycle выполнения.

При попытке использовать внутри Celery `worker` `async DB resources`, 
созданные для FastAPI-приложения, возникали ошибки:
- `got Future attached to a different loop`;
- `Event loop is closed`.

`AsyncEngine`, `connection pool` и связанные `async resources` могут быть связаны с `event loop`, 
в контексте которого они используются.

Поэтому переиспользование одной `DB infrastructure` между FastAPI и Celery 
приводит к проблемам при работе с `async PostgreSQL`.

---


## Принятое решение

Разделить `DB infrastructure` FastAPI и Celery `worker`.

FastAPI использует собственные:
```text
FastAPI
├── AsyncEngine
├── AsyncSession factory (AsyncSessionLocal)
└── request-scoped AsyncSession
```

Celery `worker` использует отдельные:
```text
Celery Worker
├── AsyncEngine
├── AsyncSession factory (WorkerAsyncSessionLocal)
└── task-scoped AsyncSession
```

`Celery task` получает только необходимые данные для запуска бизнес-сценария, например `task_id`, 
после чего создает `AsyncSession` в собственном `runtime context`.

Созданная `session` передается в `AnalyzerService`:
```text
Celery Task -> Worker AsyncSession -> AnalyzerService -> Repositories -> Postgres
```

Таким образом, FastAPI и Celery используют одну БД Postgres, 
но не переиспользуют между собой `AsyncSession`, `connection pool` 
или другие асинхронные ресурсы, привязанные к конкретному циклу событий.

Бизнес-логика при этом остается общей и реализуется в `AnalyzerService`.

---


## Результаты

### Положительные
- исключается совместное использование асинхронных ресурсов БД между разными `event loops`;
- устраняются ошибки, связанные с использованием `Future` в другом `event loop`;
- lifecycle подключений к БД в Celery не зависит от FastAPI;
- `AnalyzerService` остается общим для FastAPI и Celery;
- Celery `worker` самостоятельно управляет своими database connections.

### Отрицательные
- FastAPI и Celery имеют отдельную `database infrastructure`;
- увеличивается количество `connection pools`;
- необходимо отдельно управлять lifecycle ресурсов `worker`.

### Ограничения
FastAPI и Celery не должны передавать друг другу:
- `AsyncSession`;
- открытые `database connections`;
- другие `async resources`, связанные с `event loop`.

При настройке PostgreSQL необходимо учитывать суммарное количество `connections` из FastAPI и Celery worker.

---


## Заметки

Разделение относится к `infrastructure layer` и не требует дублирования бизнес-логики.
```text
FastAPI ──┐
          ├──> AnalyzerService
Celery ───┘
```
Каждый runtime создает собственную `AsyncSession`, но использует общий `Service` и `Repository layers`.

---


## Возможные альтернативы

### Использовать общую database infrastructure FastAPI и Celery
__Преимущества__:
- меньше инфраструктурного кода;
- одна конфигурация подключения.

__Недостатки__:
- `async resources` могут использоваться в разных `event loops`;
- возникали ошибки `got Future attached to a different loop`;
- возможны ошибки `Event loop is closed`;
- lifecycle ресурсов FastAPI и Celery становится связанным.

### Использовать синхронный SQLAlchemy внутри Celery
__Преимущества__:
- отсутствует проблема привязки `async DB resources` к `event loop`;
- проще lifecycle `DB session` внутри `worker`.

__Недостатки__:
- появляется второй способ работы с PostgreSQL;
- необходимо поддерживать одновременно `sync` и `async` доступ к БД;
- нарушается единый подход к работе с БД в приложении.

---
