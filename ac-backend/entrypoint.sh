#!/bin/sh

alembic upgrade head
fastapi run /app/src/main.py --port 8082 --host 0.0.0.0
