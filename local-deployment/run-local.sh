#!/usr/bin/env bash
set -e

COMPOSE_DIR="../deployment"

# Load all values from the .env file
set -a
source "$COMPOSE_DIR/.env"
set +a

# Override env variables
export PRODUCTION=false

# Run compose from the directory with compose.yml
cd "$COMPOSE_DIR"
podman-compose up -d
