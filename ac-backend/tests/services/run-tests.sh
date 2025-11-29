#!/usr/bin/env bash

set -a # automatically export all variables
source .env # read variables from .env
set +a

podman-compose down -v
podman-compose up -d

echo "Waiting for postgres..."

until podman exec ac-test-database pg_isready -U postgres; do
    sleep 0.5
done

echo "PostgreSQL started"

BACKEND_DIR="../.."
cd "$BACKEND_DIR"

source .venv/bin/activate
alembic upgrade head

cd "plugins"
# remove every file except for __init__.py
ls | grep -P "^(?!__init__\.py).*$" | xargs -d"\n" rm -rf

cd ../resources
# remove all previous resource files
rm -rf *

cd ../logs
rm -fr *

cd ..

cd tests/services
uv run pytest -q ..
