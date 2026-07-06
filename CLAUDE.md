# CLAUDE.md

Guidance for working in this repository.

## Project

Mink is a social payments API (FastAPI + Motor/MongoDB). The backend owns identity, social,
activity, notifications, and AI features; the blockchain only settles payments. See
`features.txt` for the product/domain vision.

## Stack

- FastAPI, served via `main.py` (uvicorn)
- MongoDB via Motor (`api/database.py` — `db` singleton, `get_db()` FastAPI dependency)
- Pydantic Settings for config (`api/v1/utils/config.py` — `config` singleton)
- Structured JSON logging (`api/v1/utils/logger.py` — `get_logger(name)`)
- Package manager: `uv` (see `pyproject.toml`, `uv.lock`)

## Directory layout

```
api/
  database.py         MongoDB connection manager (singleton: db)
  indexes.py           create_indexes() — index setup run at startup
  response.py           success_response() — shared success envelope
  v1/
    routes/            APIRouter endpoints — wiring only
    services/          business logic, one class per file, singleton instance
    schemas/           Pydantic request/response body shapes
    models/            database document structures
    dependencies/      FastAPI dependencies (auth, pagination, etc.)
    middlewares/        cross-cutting request handling (errors, logging)
    utils/             config, logger, generic helpers
```

## Architectural rules

- **One thing per file.** Each file has a single responsibility — a route file wires
  endpoints, a service file holds logic, a schema file defines shapes, a model file defines
  storage structure. Don't mix concerns into one file for convenience.

- **Routes are thin.** A route function should: parse/validate input (via the schema),
  call the service, and return `success_response(...)` from `api/response.py`. No business
  logic, no helper functions, no direct database calls in route files. If a route needs a
  helper, that helper belongs in the service (or a dedicated util), not inline in the route
  module.

- **Services own the logic.** Each domain gets a service file exporting a class (e.g.
  `UserService`) containing all business logic and database access for that domain. At the
  bottom of the file, instantiate a module-level singleton (e.g. `user_service =
UserService()`) and import that singleton elsewhere — mirrors the existing `db` singleton
  pattern in `api/database.py`.

  ```python
  # api/v1/services/user.py
  class UserService:
      async def get_by_handle(self, handle: str) -> dict | None:
          ...

  user_service = UserService()
  ```

- **Schemas vs. models — don't conflate them.**
  - `schemas/`: Pydantic models describing the shape of request bodies and response
    payloads (the API contract).
  - `models/`: the structure of what's actually stored in MongoDB (the persistence
    contract). These can diverge from schemas (e.g. models carry `_id`, timestamps,
    internal fields that are never exposed in a schema).

- **Responses.** Success responses always go through `success_response()` in
  `api/response.py` so every endpoint returns a uniform envelope
  (`success`, `status_code`, `message`, `data`). Do not hand-build `JSONResponse` objects in
  routes or services for the success path.

- **Errors.** Don't catch and format errors in routes/services for cases already covered by
  the global handlers in `api/v1/middlewares/errors.py` (PyMongo error families, validation
  errors, generic `HTTPException`). Raise `HTTPException` (or let PyMongo errors propagate)
  and let the registered handlers in `main.py` format the response. Only add a new handler
  in `errors.py` (and register it in `main.py`) for a genuinely new exception type.

- **Singletons over dependency injection sprawl.** Follow the `db` / service-instance
  pattern: instantiate once at module scope, import that instance elsewhere. Avoid
  re-instantiating services or the Mongo client in multiple places.

- **Logging.** Use `get_logger("<module>")` from `api/v1/utils/logger.py`, not `print` or
  the root logger, so log output stays structured JSON.
