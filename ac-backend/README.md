## Info
Built with *Python 3.13.5*, using the UV package manager

## DEV - Running the app
Start services, such as the DB
```shell
cd ../dev
podman-compose up -d
cd ../ac-backend
```
```shell
POSTGRES_USER=postgres \
POSTGRES_PASSWORD=postgres \
POSTGRES_PORT=5432 \
POSTGRES_DB=astrocollectordb \
POSTGRES_HOST=localhost \
REDIS_HOST=localhost \
REDIS_PORT=6379 \
celery -A src.core.celery.worker worker
```

Then apply migrations
```shell
POSTGRES_USER=postgres \
POSTGRES_PASSWORD=postgres \
POSTGRES_PORT=5432 \
POSTGRES_DB=astrocollectordb \
POSTGRES_HOST=localhost \
REDIS_PORT=6379 \
REDIS_HOST=localhost \
alembic upgrade head
```

Run the app with
```shell
source .venv/bin/activate
POSTGRES_USER=postgres \
POSTGRES_PASSWORD=postgres \
POSTGRES_PORT=5432 \
POSTGRES_DB=astrocollectordb \
POSTGRES_HOST=localhost \
REDIS_HOST=localhost \
REDIS_PORT=6379 \
python -m uvicorn src.main:app --reload --reload-dir src
```

## Generate migrations
When changing the DB models, generate new migration
```shell
POSTGRES_USER=postgres \
POSTGRES_PASSWORD=postgres \
POSTGRES_PORT=5432 \
POSTGRES_DB=astrocollectordb \
POSTGRES_HOST=localhost \
REDIS_HOST=localhost \
REDIS_PORT=6379 \
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

## Inspect DB
To connect to the postgres console, run
```shell
podman exec -it ac-database psql -U postgres -d astrocollectordb
```
