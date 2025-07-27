# Flask Benchmark App

This is a Flask application for benchmarking, with PostgreSQL and SQLAlchemy ORM, matching the FastAPI and Django apps in this repo.

## Prerequisites
- Python 3.8+
- PostgreSQL running and accessible
- A `.env` file with your database credentials (see below)

## Setup

1. **Install dependencies:**

```bash
pip install -r requirements.txt
```

2. **Configure environment variables:**

Create a `.env` file in the `flask/` directory with the following (edit as needed):

```
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=postgres
```

3. **Run the Flask app:**

```bash
# On Windows (PowerShell):
$env:FLASK_APP="app.py"; flask run

# Or simply:
python app.py
```

The app will be available at http://127.0.0.1:5000/

## Endpoints
- `/plain-text` — Plain text hello world
- `/json` — JSON hello world
- `/products` — POST (create), GET (list)
- `/products/<id>` — GET, PUT, DELETE
- `/fortune` — HTML page with top 100 products

## Notes
- The database tables are created automatically on first request.
- For production, use a WSGI server like Gunicorn.

---

For benchmarking, ensure your database is seeded with data as per the repo instructions.
