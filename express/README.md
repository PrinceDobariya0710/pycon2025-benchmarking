# Express Benchmark App

This is a production-ready Express.js benchmarking app using Prisma ORM and PostgreSQL, matching the endpoints and DB model of the FastAPI and Django apps in this repo.

## Prerequisites
- Node.js 18+
- PostgreSQL running and accessible
- A `.env` file with your database credentials (see below)

## Setup

1. **Install dependencies:**

```bash
cd express
npm install
```

2. **Configure environment variables:**

Edit `.env` in the `express/` directory as needed:

```
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=postgres
DATABASE_URL="postgresql://postgres:postgres@localhost:5432/postgres?schema=public"
```

3. **Set up the database and Prisma:**

```bash
npx prisma generate
npx prisma migrate dev --name init
```

4. **Run the app:**

```bash
npm run dev
# or for production
npm start
```

The app will be available at http://localhost:3000/

## Endpoints
- `/plain-text` — Plain text hello world
- `/json` — JSON hello world
- `/products` — POST (create), GET (list)
- `/products/:id` — GET, PUT, DELETE
- `/fortune` — HTML page with top 100 products

## Notes
- Prisma schema is in `prisma/schema.prisma`.
- EJS template for `/fortune` is in `src/views/fortune.ejs`.
- For production, use a process manager like PM2 or Docker.

---

For benchmarking, ensure your database is seeded with data as per the repo instructions.
