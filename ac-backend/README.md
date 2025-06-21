## Info
Built with *Python 3.13.5*, using the UV package manager

## DEV - Running the app
Start services, such as the DB
```shell
cd ../podman
podman-compose up -d
cd ../ac-backend
```

Then apply migrations
```shell
alembic upgrade head
```

Run the app with
```shell
source .venv/bin/activate
python -m uvicorn src.main:app --reload
```

## Generate migrations
When changing the DB models, generate new migration
```shell
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
