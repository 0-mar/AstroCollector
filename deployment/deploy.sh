#!/usr/bin/env bash

# execute the script from astrocollector/deployment directory

BACKEND_SRC_DIR="../ac-backend"
FRONTEND_SRC_DIR="../ac-frontend"

BACKEND_TARGET_DIR="astrocollector-src/ac-backend"
FRONTEND_TARGET_DIR="astrocollector-src/ac-frontend"
DEPLOYMENT_TARGET_DIR="astrocollector-src/deployment"

mkdir -p "${BACKEND_TARGET_DIR}"
mkdir -p "${FRONTEND_TARGET_DIR}"
mkdir -p "${DEPLOYMENT_TARGET_DIR}"

mkdir -p "${BACKEND_TARGET_DIR}/plugins"

copy_be_files()
{
  FILE=$1
  cp -r "${BACKEND_SRC_DIR}/${FILE}" "${BACKEND_TARGET_DIR}/${FILE}"
}

copy_fe_files()
{
  FILE=$1
  cp -r "${FRONTEND_SRC_DIR}/${FILE}" "${FRONTEND_TARGET_DIR}/${FILE}"
}

echo "Preparing source files..."

be_files=("alembic" "plugins/__init__.py" "src" "tests" ".dockerignore" ".env" "alembic.ini" "Dockerfile" "entrypoint.sh" "pyproject.toml" "uv.lock")
for fname in "${be_files[@]}"
do
    copy_be_files "$fname"
done

fe_files=("components" "lib" "public" "src" ".dockerignore" ".env.production" "Dockerfile" "nginx.local.conf" "nginx.prod.conf" "index.html" "package.json" "package-lock.json" "tsconfig.json" "vite.config.ts")
for fname in "${fe_files[@]}"
do
    copy_fe_files "$fname"
done

cp "compose.yml" "${DEPLOYMENT_TARGET_DIR}/compose.yml"
cp ".env" "${DEPLOYMENT_TARGET_DIR}/.env"
# always set PRODUCTION to True
sed -i -E 's/^\s*PRODUCTION\s*=\s*false\s*$/PRODUCTION=true/' "${DEPLOYMENT_TARGET_DIR}/.env"

echo "Deleting old files on the server..."
ssh xmarek9@phoenix 'cd ~/astrocollector-src/deployment && podman-compose down -v; cd ~; rm -rf astrocollector-src; rm -rf ac-resources/*'

echo "Sending source files to the server..."
scp -r astrocollector-src xmarek9@phoenix:~

echo "Deploying containers on the server..."
ssh xmarek9@phoenix 'cd ~/astrocollector-src/deployment; podman-compose build --no-cache && podman-compose up -d'

rm -rf "astrocollector-src"
