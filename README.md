# CarbonLedger

A Django REST + React app for ingesting, normalizing, and reviewing ESG emissions data from enterprise clients.

## How to run locally with Docker

1. Copy the env file and fill in any values you want to change:

```bash
cp .env.example .env
```

2. Start everything:

```bash
docker compose up --build
```

This starts Postgres on port 5432, the Django backend on port 8000, and the React dev server on port 5173.

3. Create a superuser so you can log in:

```bash
docker compose exec backend python manage.py createsuperuser
```

4. Open http://localhost:5173 and log in with the superuser credentials.

## How to run locally without Docker

You need Postgres running locally with a database called `carbonledger`.

```bash
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env  # edit DB credentials
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

```bash
# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

## Running tests

```bash
cd backend
../.venv/bin/pytest tests/ -v
```

## Admin panel

Go to http://localhost:8000/admin and log in with your superuser. From there you can create Tenant records, inspect batches, and manage users.

## Default tenant

After creating a superuser, go to the admin panel and create a Tenant with id=1. The frontend hardcodes `tenant_id=1` for now.

## Deployment on Render

1. Create a Render account.
2. Create a new PostgreSQL database on Render. Copy the internal connection URL.
3. Create a new Web Service pointing at this repo, root dir `backend`, build command `pip install -r requirements.txt`, start command `python manage.py migrate && gunicorn config.wsgi:application`.
4. Add environment variables: `SECRET_KEY`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`.
5. Create a Static Site for the frontend, root dir `frontend`, build command `npm install && npm run build`, publish dir `dist`.
