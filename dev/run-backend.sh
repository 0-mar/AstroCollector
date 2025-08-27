#!/usr/bin/env bash

podman-compose down -v
podman-compose up -d

echo "Waiting for postgres..."


#while ! nc -z localhost 5432; do
#  sleep 0.5
#done
#sleep 1

until podman exec ac-database pg_isready -U postgres; do
    sleep 0.5
done

echo "PostgreSQL started"

set -a # automatically export all variables
source .env # read variables from .env
set +a

BACKEND_DIR="../ac-backend"
cd "$BACKEND_DIR"

source .venv/bin/activate
alembic upgrade head

cd "plugins"

# remove every file except for __init__.py
ls | grep -P "^(?!__init__\.py).*$" | xargs -d"\n" rm -rf

cd ..
python -m uvicorn src.main:app --reload --reload-dir src
