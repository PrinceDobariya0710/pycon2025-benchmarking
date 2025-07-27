import asyncio
import httpx
import time
import csv
import os
import random
import statistics
import json
from pathlib import Path
import psycopg2
from python_on_whales import DockerClient
from dotenv import load_dotenv

load_dotenv(".env")
# === CONFIGURATION ===
docker = DockerClient(compose_files=["docker-compose.yml"])

# Path to CSV with product data (assumes mounted in Docker or present locally)
DATA_PATH = Path("data/products.csv")
OUTPUT_PATH = Path("results/benchmark_results.csv")

# Load from environment variables
FRAMEWORKS = json.loads(
    os.getenv("FRAMEWORKS_JSON", "{}")
)  # Example: {"FastAPI": "http://fastapi:8000"}
CONCURRENCY = int(os.getenv("CONCURRENCY", 100))
TOTAL_REQUESTS = int(os.getenv("TOTAL_REQUESTS", 500))

FRAMEWORK_SERVICES = ["flask", "django", "fastapi", "fastapi-sync", "express", "gin"]
DB_SERVICE = "db"


# === LOAD PRODUCTS FROM CSV ===


def load_products():
    with open(DATA_PATH, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        # Only keep the required fields for each product
        fields = [
            "name",
            "description",
            "brand",
            "category",
            "price",
            "currency",
            "stock",
            "ean",
            "color",
            "size",
            "availability",
            "internal_id",
        ]
        return [{k: row[k] for k in fields} for row in reader]


# === DEFINE TEST CASES ===

TEST_CASES = [
    {"name": "PlainText", "method": "GET", "path": "/ping", "payload": None},
    {
        "name": "JSON Echo",
        "method": "POST",
        "path": "/echo",
        "payload": {"name": "Test", "value": 123},
    },
    {
        "name": "Create Product",
        "method": "POST",
        "path": "/products",
        "payload": "dynamic",
    },  # From CSV
    {"name": "Get Product", "method": "GET", "path": "/products/{id}", "payload": None},
    {"name": "List Products", "method": "GET", "path": "/products", "payload": None},
    {
        "name": "Update Product",
        "method": "PUT",
        "path": "/products/{id}",
        "payload": "dynamic",
    },
    {"name": "Fortune 100", "method": "GET", "path": "/fortune", "payload": None},
    {
        "name": "Delete Product",
        "method": "DELETE",
        "path": "/products/{id}",
        "payload": None,
    },
]


# === HTTP REQUEST WRAPPER ===


async def make_request(client, method, url, payload=None):
    start = time.time()
    try:
        if method == "GET":
            res = await client.get(url)
        elif method == "POST":
            res = await client.post(url, json=payload)
        elif method == "PUT":
            res = await client.put(url, json=payload)
        elif method == "DELETE":
            res = await client.delete(url)
        else:
            return -1, 0
        duration = (time.time() - start) * 1000  # in milliseconds
        return duration, res.status_code
    except Exception:
        return -1, 0


# Helper: add trailing slash for Django endpoints
def add_trailing_slash_if_django(framework, path):
    # If the framework name contains 'django', add trailing slash if not present
    if "django" in framework.lower() and not path.endswith("/"):
        return path + "/"
    return path


# === BENCHMARK SINGLE TEST CASE ===
async def run_test_case(framework, base_url, case, products):
    print(f"🔄 Running {case['name']} for {framework}")
    durations = []
    status_codes = []

    async with httpx.AsyncClient() as client:
        sem = asyncio.Semaphore(CONCURRENCY)

        async def bound_request(_):
            async with sem:
                # Use helper to add trailing slash for Django endpoints
                url = base_url + add_trailing_slash_if_django(framework, case["path"])
                payload = None
                # Special handling for PlainText and JSON Echo
                if case["name"] == "PlainText":
                    dur, status = await make_request(
                        client,
                        "GET",
                        base_url
                        + add_trailing_slash_if_django(framework, "/plain-text"),
                    )

                elif case["name"] == "JSON Echo":
                    dur, status = await make_request(
                        client,
                        "GET",
                        base_url + add_trailing_slash_if_django(framework, "/json"),
                    )

                elif case["name"] == "Create Product":
                    payload = random.choice(products)
                    dur, status = await make_request(client, "POST", url, payload)

                elif "{id}" in case["path"]:
                    product_id = random.randint(1, len(products))
                    url = base_url + add_trailing_slash_if_django(
                        framework, case["path"].replace("{id}", str(product_id))
                    )
                    if case["payload"] == "dynamic":
                        if case["name"] == "Update Product":
                            payload = {"name": f"Updated {random.randint(1, 10000)}"}
                else:
                    if case["payload"] == "dynamic":
                        if case["name"] == "Create Product":
                            payload = random.choice(products)
                    else:
                        payload = case["payload"]

                if case["name"] not in [
                    "PlainText",
                    "JSON Echo",
                    "Create Product",
                ] and not (case["name"] == "Create Product"):
                    dur, status = await make_request(
                        client, case["method"], url, payload
                    )
                if dur != -1:
                    durations.append(dur)
                    status_codes.append(status)

        tasks = [bound_request(i) for i in range(TOTAL_REQUESTS)]
        await asyncio.gather(*tasks)

    if not durations:
        return None

    return {
        "framework": framework,
        "endpoint": case["path"],
        "method": case["method"],
        "test_type": case["name"],
        "concurrency": CONCURRENCY,
        "total_requests": TOTAL_REQUESTS,
        "avg_response_time_ms": round(statistics.mean(durations), 2),
        "p95_response_time_ms": round(statistics.quantiles(durations, n=100)[94], 2),
        "p99_response_time_ms": round(statistics.quantiles(durations, n=100)[98], 2),
        "throughput_rps": round(1000 * len(durations) / sum(durations), 2),
        "success_rate_percent": round(
            (sum(1 for s in status_codes if 200 <= s < 300) / TOTAL_REQUESTS) * 100, 2
        ),
        "error_count": TOTAL_REQUESTS - len(status_codes),
    }


# === DATABASE SEEDING (Postgres Direct) ===


def seed_database_postgres(products):
    """
    Seed the PostgreSQL database directly using psycopg2.
    Expects DB connection info in environment variables:
      POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB
    Checks and creates the 'product' table if it does not exist.
    Ignores the CSV 'index' column.
    """
    import os

    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", 5432),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "root"),
        dbname=os.getenv("POSTGRES_DB", "benchmark_db"),
    )
    cur = conn.cursor()
    try:
        # Create table if not exists
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS product (
                id SERIAL PRIMARY KEY,
                name TEXT,
                description TEXT,
                brand TEXT,
                category TEXT,
                price NUMERIC,
                currency TEXT,
                stock INTEGER,
                ean TEXT,
                color TEXT,
                size TEXT,
                availability TEXT,
                internal_id TEXT
            );
        """
        )
        conn.commit()
        # Truncate table
        cur.execute("TRUNCATE TABLE product RESTART IDENTITY CASCADE;")
        # Bulk insert
        for prod in products:
            cur.execute(
                "INSERT INTO product (name, description, brand, category, price, currency, stock, ean, color, size, availability, internal_id) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);",
                (
                    prod["name"],
                    prod["description"],
                    prod["brand"],
                    prod["category"],
                    prod["price"],
                    prod["currency"],
                    prod["stock"],
                    prod["ean"],
                    prod["color"],
                    prod["size"],
                    prod["availability"],
                    prod["internal_id"],
                ),
            )
        conn.commit()
        print("✅ Database seeded via psycopg2 (table checked/created if needed)")
        return True
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()


def stop_and_remove_all_services():
    print("Stopping all running containers...")
    docker.compose.down(remove_orphans=True, volumes=False)


def start_service(service):
    print(f"Starting {service} container...")
    docker.compose.up(detach=True, services=[service])
    # Optionally, wait for the service to be ready
    time.sleep(5)  # Replace with health check if needed


def stop_and_remove_service(service):
    print(f"Stopping and removing {service} container...")
    docker.compose.stop(services=[service])
    docker.compose.rm(services=[service])


# === MAIN RUNNER ===


async def main():
    products = load_products()
    seeded = seed_database_postgres(products)
    results = []

    # Start only the DB container first
    print("\n=== Starting DB container ===")
    # docker.compose.up(detach=True, services=[DB_SERVICE])
    time.sleep(5)  # Wait for DB to be ready

    # Split test cases by DB requirement
    non_db_cases = [
        c
        for c in TEST_CASES
        if c["name"] in ["PlainText", "JSON Echo", "Create Product"]
    ]
    db_cases = [
        c
        for c in TEST_CASES
        if c["name"]
        not in ["PlainText", "JSON Echo", "Create Product", "Delete Product"]
    ]
    delete_case = next(c for c in TEST_CASES if c["name"] == "Delete Product")

    stop_and_remove_all_services()  # Ensure clean state before starting

    for service in FRAMEWORK_SERVICES:
        start_service(service)
        framework = service.capitalize() if service != "express" else "Express"
        base_url = FRAMEWORKS.get(framework)
        if not base_url:
            print(f"⚠️ Skipping {framework}: No base URL configured.")
            stop_and_remove_service(service)
            continue
        async with httpx.AsyncClient() as client:
            # 1. Run non-DB tests (PlainText, JSON Echo, Create Product)
            for case in non_db_cases:
                result = await run_test_case(framework, base_url, case, products)
                if result:
                    results.append(result)

            # 2. Seed DB before DB-dependent tests (directly via psycopg2)
            seeded = seed_database_postgres(products)
            if not seeded:
                print(f"⚠️ Skipping DB-dependent tests for {framework} (seeding failed)")
                stop_and_remove_service(service)
                continue

            # 3. Run DB-dependent tests (Get, List, Update, Fortune 100)
            for case in db_cases:
                result = await run_test_case(framework, base_url, case, products)
                if result:
                    results.append(result)

            # 4. Run Delete Product last
            result = await run_test_case(framework, base_url, delete_case, products)
            if result:
                results.append(result)

        stop_and_remove_service(service)
        time.sleep(2)  # Small delay between containers

    # Optionally stop DB at the end
    # docker.compose.stop(services=[DB_SERVICE])
    # docker.compose.rm(services=[DB_SERVICE], force=True)

    if results:
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_PATH, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
            writer.writeheader()
            writer.writerows(results)

    print(f"\n✅ Benchmarking complete. Results saved to: {OUTPUT_PATH}")


# === ENTRY POINT ===
if __name__ == "__main__":
    asyncio.run(main())
