# sqlalchemy-session-proxy

A lightweight proxy for SQLAlchemy sessions that provides a **unified interface** over both synchronous (`Session`) and asynchronous (`AsyncSession`) usage.

This library allows you to write database-access code that works in **both sync and async environments** with minimal branching, while still respecting SQLAlchemy’s execution model.

---

## Features

- **Unified API** for `Session` and `AsyncSession`
- **Automatic async detection** via `is_async`
- **Explicit dispatching** to sync or async implementations
- **Async-compatible method signatures** for mixed environments
- **Fully type-annotated** for IDEs and static analysis
- **No hidden magic** beyond SQLAlchemy’s own async design

---

## Installation

```bash
pip install sqlalchemy-session-proxy
````

---

## Basic Usage

```python
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy_session_proxy.session_proxy import SqlalchemySessionProxy
```

### Synchronous Session

```python
session = Session(...)
proxy = SqlalchemySessionProxy(session)

proxy.add(obj)
proxy.commit()

result = proxy.execute(statement)
```

### Asynchronous Session

```python
async def main():
    async_session = AsyncSession(...)
    proxy = SqlalchemySessionProxy(async_session)

    proxy.add(obj)          # NOT awaitable (by SQLAlchemy design)
    await proxy.commit()    # awaitable

    result = await proxy.execute(statement)
```

> ⚠️ **Important**
>
> Some methods (such as `add`, `add_all`, `expire`) are **synchronous by design** even when used with `AsyncSession`.
> This behavior follows SQLAlchemy’s official API.

---

## Unified Execution Pattern

The following methods automatically dispatch based on the session type:

```python
result = await proxy.execute(stmt)
rows = await proxy.scalars(stmt)
value = await proxy.scalar(stmt)
obj = await proxy.get(User, user_id)
```

* In **sync mode**, these methods do not require `await`
* In **async mode**, they must be awaited

---

## API Overview

### Core Properties

* `SqlalchemySessionProxy(session)`
* `.session` — underlying `Session` or `AsyncSession`
* `.is_async` — `True` if using `AsyncSession`

---

## Method Compatibility Matrix

| Method                  | Sync | Async | Notes                  |
| ----------------------- | ---- | ----- | ---------------------- |
| `add`                   | ✔️   | ✔️    | Not awaitable          |
| `add_all`               | ✔️   | ✔️    | Not awaitable          |
| `commit`                | ✔️   | ✔️    | Awaitable in async     |
| `rollback`              | ✔️   | ✔️    | Awaitable in async     |
| `close`                 | ✔️   | ✔️    | Awaitable in async     |
| `flush`                 | ✔️   | ✔️    | Awaitable in async     |
| `merge`                 | ✔️   | ✔️    | Awaitable in async     |
| `delete`                | ✔️   | ✔️    | Awaitable in async     |
| `get`                   | ✔️   | ✔️    | Awaitable in async     |
| `get_one`               | ✔️   | ✔️    | Awaitable in async     |
| `execute`               | ✔️   | ✔️    | Awaitable in async     |
| `scalars`               | ✔️   | ✔️    | Awaitable in async     |
| `scalar`                | ✔️   | ✔️    | Awaitable in async     |
| `refresh`               | ✔️   | ✔️    | Awaitable in async     |
| `expire`                | ✔️   | ✔️    | Not awaitable          |
| `expire_all`            | ✔️   | ✔️    | Not awaitable          |
| `expunge`               | ✔️   | ✔️    | Not awaitable          |
| `expunge_all`           | ✔️   | ✔️    | Not awaitable          |
| `is_modified`           | ✔️   | ✔️    | Not awaitable          |
| `in_transaction`        | ✔️   | ✔️    | Not awaitable          |
| `in_nested_transaction` | ✔️   | ✔️    | Not awaitable          |
| `query`                 | ✔️   | ❌     | Sync-only (legacy API) |
| `stream`                | ❌    | ✔️    | Async-only             |
| `stream_scalars`        | ❌    | ✔️    | Async-only             |
| `run_sync`              | ❌    | ✔️    | Async-only             |

---

## Notes on `query()`

* `query()` is **sync-only**
* Calling it on an `AsyncSession` proxy raises `NotImplementedError`
* This mirrors SQLAlchemy’s own guidance:

  * `Query` is **legacy**
  * Prefer `select()` for new code

---

## `run_sync`

```python
def legacy_fn(session: Session, value: str) -> str:
    session.add(MyModel(name=value))
    session.flush()
    return "ok"

async def main():
    async with AsyncSession(engine) as session:
        proxy = SqlalchemySessionProxy(session)
        result = await proxy.run_sync(legacy_fn, "test")
```

* Runs synchronous ORM logic inside async code
* Uses SQLAlchemy’s greenlet bridge
* Available **only** for `AsyncSession`

---

## License

Apache-2.0

---

## Author

Tercel ([tercel.yi@gmail.com](mailto:tercel.yi@gmail.com))

---

## Links

* **GitHub**: [https://github.com/aipartnerup/sqlalchemy-session-proxy](https://github.com/aipartnerup/sqlalchemy-session-proxy)
* **PyPI**: [https://pypi.org/project/sqlalchemy-session-proxy/](https://pypi.org/project/sqlalchemy-session-proxy/)
* **Issues**: [https://github.com/aipartnerup/sqlalchemy-session-proxy/issues](https://github.com/aipartnerup/sqlalchemy-session-proxy/issues)
* **Discussions**: [https://github.com/aipartnerup/sqlalchemy-session-proxy/discussions](https://github.com/aipartnerup/sqlalchemy-session-proxy/discussions)
