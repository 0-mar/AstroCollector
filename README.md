# AstroCollector
AstroCollector is a web application to collect, unify, display and export photometric data from various star survey archives.

The app is split into three modules:
- ac-frontend
- ac-backend
- deployment

## ac-frontend
This module contains the frontend part of the application. See the README for details on running the frontend.

## ac-backend
This module contains the backend part of the application. See the README for details on running the server.

## deployment
This module is split into three directories:
- deployment
- dev
- local-deployment

### deployment directory
This directory contains a compose file and a deployment script, which builds and deploys the application on the production server.

To deploy the application on the server, please follow those steps:

1. Rename the `.env.example` file to `.env`
2. Configure the env values as you wish
3. Run the deploy script:
 ```shell
 chmod +x deploy.sh
 ./deploy.sh
 ```

### dev directory
This directory contains a `compose.yml` file and a deployment script, which runs the application in development mode.

To run the application in the dev mode, please follow those steps:

1. Rename the `.env.example` file to `.env`
2. Configure the env values as you wish
3. Run the backend script:
 ```shell
 chmod +x run-backend.sh
 ./run-backend.sh
 ```
4. Run frontend from the `ac-frontend` directory:
```shell
npm run dev
```

Unlike the server-deployed app, the dev `compose.yml` contains fewer services - the PostgreSQL database, Redis broker and Redis in-memory database. FastAPI and Celery are directly run as processes on the host machine.

## local-deployment
This directory contains a script to build and run the app in the same way as it is on the production server. All of the services are ran in separate containers, The nginx container emulates the reverse proxy, which is used in production.

## env variables
For description of env variables, please see the respective `.env` files.
