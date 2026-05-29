# CarbonLedger

A Django REST + React app for ingesting, normalizing, and reviewing ESG emissions data from enterprise clients.

## Login credentials

Two users are seeded automatically on first startup:

| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | Superuser, full access |
| analyst | analyst123 | Standard analyst user |

Use either to log in at http://localhost:5173.

## How to run locally with Docker

1. Copy the env file:

```bash
cp .env.example .env
```

2. Start everything:

```bash
docker compose up --build
```

This starts Postgres on port 5432, the Django backend on port 8000, and the React dev server on port 5173. On first boot, migrations run and the default users and tenant are seeded automatically.

3. Open http://localhost:5173 and log in with `admin / admin123` or `analyst / analyst123`.

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
python manage.py seed       # creates default users and tenant
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

Go to http://localhost:8000/admin and log in with `admin / admin123`. The seed command creates a tenant called "Acme Corp" with id=1, which is what the frontend uses.

## Deployment on Render

1. Create a Render account.
2. Create a new PostgreSQL database on Render. Copy the internal connection URL.
3. Create a new Web Service pointing at this repo, root dir `backend`, build command `pip install -r requirements.txt`, start command `python manage.py migrate && gunicorn config.wsgi:application`.
4. Add environment variables: `SECRET_KEY`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`.
5. Create a Static Site for the frontend, root dir `frontend`, build command `npm install && npm run build`, publish dir `dist`.
