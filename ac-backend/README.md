## Backend module
The app is built with *Python 3.13.5*, using the UV package manager. The API is built using the FastAPI framework.
Other used services are Celery, Celery beat and Redis.

### `tests` directory
The directory contains tests. Run the tests using the `run-tests.sh` file, located in `tests/services`.

### `logs` directory
This directory contains logs

## Setup
Create a virtual environment in the `ac-backend` directory, install `uv` package manager and download all packages.

```shell
python -m venv .venv
source .venv/bin/activate
pip install uv
uv sync --frozen --no-cache
```

## DEV - Running the app
Run the application using the `run-backend.sh` file in the `dev` directory, or manually by following these steps:

1. Start services by running:
```shell
cd ../dev
podman-compose down -v
podman-compose up -d
cd ../ac-backend
```

2. Run Celery
```shell
PRODUCTION=false \
POSTGRES_USER=postgres \
POSTGRES_PASSWORD=postgres \
POSTGRES_PORT=5432 \
POSTGRES_DB=astrocollectordb \
POSTGRES_HOST=localhost \
REDIS_BROKER_HOST=localhost \
REDIS_BROKER_PORT=6379 \
REDIS_DB_HOST=localhost \
REDIS_DB_PORT=6380 \
celery -A src.core.celery.worker worker
```

3. Run Celery Beat:
```shell
PRODUCTION=false \
POSTGRES_USER=postgres \
POSTGRES_PASSWORD=postgres \
POSTGRES_PORT=5432 \
POSTGRES_DB=astrocollectordb \
POSTGRES_HOST=localhost \
REDIS_BROKER_HOST=localhost \
REDIS_BROKER_PORT=6379 \
REDIS_DB_HOST=localhost \
REDIS_DB_PORT=6380 \
celery -A src.core.celery.worker beat
```

4. Apply migrations:
```shell
PRODUCTION=false \
POSTGRES_USER=postgres \
POSTGRES_PASSWORD=postgres \
POSTGRES_PORT=5432 \
POSTGRES_DB=astrocollectordb \
POSTGRES_HOST=localhost \
REDIS_BROKER_PORT=6379 \
REDIS_BROKER_HOST=localhost \
REDIS_DB_HOST=localhost \
REDIS_DB_PORT=6380 \
alembic upgrade head
```

5. Run the app:
```shell
source .venv/bin/activate
PRODUCTION=false \
POSTGRES_USER=postgres \
POSTGRES_PASSWORD=postgres \
POSTGRES_PORT=5432 \
POSTGRES_DB=astrocollectordb \
POSTGRES_HOST=localhost \
REDIS_BROKER_HOST=localhost \
REDIS_BROKER_PORT=6379 \
REDIS_DB_HOST=localhost \
REDIS_DB_PORT=6380 \
python -m uvicorn src.main:app --reload --reload-dir src
```

## Generate migrations
When changing the DB models, generate new migration
```shell
PRODUCTION=false \
POSTGRES_USER=postgres \
POSTGRES_PASSWORD=postgres \
POSTGRES_PORT=5432 \
POSTGRES_DB=astrocollectordb \
POSTGRES_HOST=localhost \
REDIS_BROKER_HOST=localhost \
REDIS_BROKER_PORT=6379 \
REDIS_DB_HOST=localhost \
REDIS_DB_PORT=6380 \
alembic revision --autogenerate -m "your message"
```

## Configure pre-commit hook
First, make sure to run this command
```shell
chmod +x run-mypy
```
to be able to use mypy

Check all files in the repo by running
```shell
source .venv/bin/activate
pre-commit run --all-files
```
After making any changes to the pre commit config file, run
```shell
pre-commit install
```

## Inspect the DB
To connect to the postgres console, run
```shell
podman exec -it ac-database psql -U postgres -d astrocollectordb
```
