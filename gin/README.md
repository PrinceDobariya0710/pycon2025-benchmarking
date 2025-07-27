# Gin Benchmark App

This is a production-ready Gin (Go) benchmarking app using GORM ORM and PostgreSQL, matching the endpoints and DB model of the FastAPI, Django, Flask, and Express apps in this repo.

## Prerequisites
- Go 1.22+
- PostgreSQL running and accessible
- A `.env` file with your database credentials (see below)

## Setup

1. **Install dependencies:**

```bash
cd gin
go mod tidy
```

2. **Configure environment variables:**

Edit `.env` in the `gin/` directory as needed:

```
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=root
POSTGRES_DB=benchmark_db
PORT=8080
```

3. **Run the app:**

```bash
go run main.go
```

The app will be available at http://localhost:8080/

## Endpoints
- `/plain-text` — Plain text hello world
- `/json` — JSON hello world
- `/products` — POST (create), GET (list)
- `/products/:id` — GET, PUT, DELETE
- `/fortune` — HTML page with top 100 products

## Notes
- GORM model is in `main.go`.
- HTML template for `/fortune` is in `templates/fortune.html`.
- For production, use a process manager or Docker.

---

For benchmarking, ensure your database is seeded with data as per the repo instructions.
