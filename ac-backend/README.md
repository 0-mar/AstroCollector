## Info
Built with *Python 3.13.5*, using the UV package manager 

## DEV - Running the app
Start services, such as the DB
```sh
cd ../podman
podman-compose up -d
cd ../ac-backend
```

Then apply migrations
```sh
alembic upgrade head
```

Run the app with
```sh
source .venv/bin/activate
python -m uvicorn src.main:app --reload 
```

## Generate migrations
When changing the DB models, generate new migration
```sh
alembic revision --autogenerate -m "your message"
```