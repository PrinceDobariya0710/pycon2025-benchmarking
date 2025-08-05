from copy import copy
import os
import json
import subprocess
import csv
import random
import time
from pathlib import Path
from dotenv import load_dotenv
import psycopg2
import httpx
from python_on_whales import DockerClient

# Load environment variables
load_dotenv(".docker.env", override=True)

# --- CONFIGURATION ---
DOCKER_COMPOSE_FILE = os.getenv("DOCKER_COMPOSE_FILE", "docker-compose.benchmark.yml")
docker = DockerClient(compose_files=[DOCKER_COMPOSE_FILE])

FRAMEWORKS = json.loads(os.getenv("FRAMEWORKS_JSON", "{}"))
# For conference benchmarks:
# - Duration: 60 seconds to get stable results and account for any JIT warmup
# - Concurrency: Test with different loads to show scaling characteristics
DURATION = os.getenv("DURATION_SECONDS", "60")  # 1 minute per test for stable results
CONCURRENCY = os.getenv("CONCURRENCY", "50")
THREADS = os.getenv("THREADS", "2")
DATA_PATH = Path("data/products.csv")
OUTPUT_PATH = Path("results/benchmark_wrk_results_gunicorn_fastapi.csv")
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

FRAMEWORK_SERVICES = [
    "flask",
    "django",
    "fastapi-uvicorn",
    "fastapi-uvicorn-sync",
    "fastapi-gunicorn",
    "fastapi-gunicorn-sync",
    "express",
    "gin",
]
DB_SERVICE = "db"

# --- TEST CASES ---
TEST_CASES = [
    {"name": "PlainText", "method": "GET", "path": "/plain-text"},
    {"name": "JSON Echo", "method": "GET", "path": "/json"},
    {"name": "Create Product", "method": "POST", "path": "/products"},
    {"name": "Get Product", "method": "GET", "path": "/products/1"},
    {"name": "List Products", "method": "GET", "path": "/products"},
    {"name": "Update Product", "method": "PUT", "path": "/products/1"},
    {"name": "Fortune 100", "method": "GET", "path": "/fortune"},
    {"name": "Delete Product", "method": "DELETE", "path": "/products/{id}"},
]

# --- LUA SCRIPTS ---
LUA_TEMPLATES = {
    "POST": """
wrk.method = "POST"
wrk.headers["Content-Type"] = "application/json"
wrk.body = '{"name":"Test Product","price":99.99,"stock":100, "description": "desc", "brand": "brand", "category": "cat", "currency": "USD", "ean": "123", "color": "red", "size": "M", "availability": "in-stock", "internal_id": "123"}'
    """,
    "PUT": """
wrk.method = "PUT"
wrk.headers["Content-Type"] = "application/json"
wrk.body = '{"name":"Updated Product"}'
    """,
    "DELETE": """
function request()
  local id = math.random(1, 10000)
  return wrk.format("DELETE", "/products/" .. id)
end
    """,
}


def write_lua_script(content, name):
    """Write a Lua script and return its path in the container's filesystem."""
    # Create lua_scripts directory if it doesn't exist
    scripts_dir = Path("lua_scripts")
    scripts_dir.mkdir(exist_ok=True)

    # Write the script to the host filesystem
    script_name = f"{name}.lua"
    host_path = scripts_dir / script_name
    with open(host_path, "w") as f:
        f.write(content.strip())

    # Return the path as it will appear inside the container
    return f"/scripts/{script_name}"


# --- DOCKER & SERVICE MANAGEMENT ---
def stop_and_remove_all_services():
    print("Stopping all running containers...")
    all_svc = copy(FRAMEWORK_SERVICES)
    all_svc.append(DB_SERVICE)
    docker.compose.down(services=all_svc, volumes=False)


def start_service(service):
    print(f"Starting {service} container...")
    docker.compose.up(detach=True, services=[service])


def stop_and_remove_service(service):
    print(f"Stopping and removing {service} container...")
    docker.compose.stop(services=[service])
    docker.compose.rm(services=[service])


def wait_for_service_ready(base_url):
    """Polls a simple endpoint to ensure the service is ready before benchmarking."""
    print(f"Waiting for {base_url} to be ready...")
    start_time = time.time()
    while time.time() - start_time < 30:  # 30-second timeout
        try:
            response = httpx.get(base_url + "/plain-text", timeout=1)
            if response.status_code == 200:
                print(f"✅ Service at {base_url} is ready.")
                return True
        except httpx.RequestError:
            pass
        time.sleep(1)
    print(f"❌ Service at {base_url} did not become ready in time.")
    return False


# --- DATABASE SEEDING ---
def seed_database_postgres(products):
    try:
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_LOCALHOST", "localhost"),
            port=os.getenv("POSTGRES_PORT", 5432),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "root"),
            dbname=os.getenv("POSTGRES_DB", "benchmark_db"),
        )
        cur = conn.cursor()
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
        cur.execute("TRUNCATE TABLE product RESTART IDENTITY CASCADE;")
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
        print("✅ Database seeded successfully.")
        return True
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        return False
    finally:
        if "conn" in locals() and conn is not None:
            cur.close()
            conn.close()


# --- WRK EXECUTION ---
def run_wrk(url, duration, concurrency, threads, lua_script_path=None):
    wrk_docker = DockerClient()

    try:
        # Ensure we have the latest wrk image
        wrk_docker.pull("openeuler/wrk:latest", quiet=True)

        # Build wrk command as a list
        command = f"wrk -d {duration}s -c {concurrency} -t {threads}"
        if lua_script_path:
            command += f" -s {lua_script_path}"
        command += f" {url}"

        print(f"🔧 Running WRK command: {command}")
        if lua_script_path:
            print(f"📜 Using Lua script at: {lua_script_path}")

        # Run using docker run command
        run_args = {
            "name": "wrk_benchmark",
            "image": "openeuler/wrk:latest",
            "command": command.split(),  # Split the command into a list
            "remove": True,
            "tty": False,
            "privileged": True,  # This might help with network access
            "networks": ["host"],
        }

        # Add volume and workdir only if we have a Lua script
        if lua_script_path:
            # Convert Windows path to proper Docker volume format
            host_path = str(Path("lua_scripts").absolute()).replace("\\", "/")
            if ":" in host_path:  # Handle Windows drive letter
                host_path = "/" + host_path.replace(":", "").lower()

            run_args["volumes"] = [(host_path, "/scripts")]
            run_args["workdir"] = "/scripts"

        # Run the container with our arguments
        output = wrk_docker.container.run(**run_args)

        # Handle output based on its type
        # Process the output
        if isinstance(output, (bytes, bytearray)):
            output_str = output.decode("utf-8").strip()
        else:
            output_str = str(output).strip()

        print("🔍 Raw output type:", type(output_str))
        print("🔍 Raw output:", output_str if output_str else "No output")

        if not output_str:
            print("⚠️ No output received from wrk")
            return "ERROR: No output received from wrk"

        return output_str

    except Exception as e:
        print(f"❌ Error running wrk: {str(e)}")
        return f"ERROR: {str(e)}"


def parse_wrk_output(output):
    if not output:
        print("⚠️ No output received from wrk")
        return None

    if isinstance(output, (bytes, bytearray)):
        output = output.decode("utf-8")

    print(
        "📊 Processing WRK output:", output[:200]
    )  # Show first 200 chars for debugging

    if "Requests/sec" not in output:
        print("⚠️ No 'Requests/sec' found in output")
        return None

    results = {}
    try:
        for line in output.splitlines():
            if "Requests/sec" in line:
                req_sec = float(line.split(":")[1].strip())
                print(f"📈 Found requests/sec: {req_sec}")
                results["requests_per_sec"] = req_sec
            elif "Latency" in line and "Thread" not in line:
                parts = [p for p in line.strip().split() if p]
                if len(parts) >= 2:
                    print(f"⏱️ Found latency: {parts[1]}")
                    results["avg_latency_ms"] = parts[1]
    except Exception as e:
        print(f"❌ Error parsing wrk output: {str(e)}")
        return None

    return results


# --- MAIN RUNNER ---
def main():
    products = [dict(p) for p in csv.DictReader(open(DATA_PATH))]
    results = []

    print("--- Starting Benchmark ---")

    # Stop everything first for a clean slate
    stop_and_remove_all_services()

    # Start DB service
    print("\n=== Starting DB container ===")
    docker.compose.up(detach=True, services=[DB_SERVICE])
    print("Waiting for DB to initialize...")
    time.sleep(10)  # Give DB time to start

    # Seed database once
    if not seed_database_postgres(products):
        print("❌ Initial database seeding failed. Aborting benchmarks.")
        docker.compose.down(remove_orphans=True)
        return

    for service in FRAMEWORK_SERVICES:
        print(f"\n📦 Benchmarking Service: {service}")
        start_service(service)

        framework_name_map = {
            "express": "express",
            "gin": "gin",
            "flask": "flask",
            "django": "django",
            "fastapi-uvicorn": "fastapi-uvicorn",
            "fastapi-uvicorn-sync": "fastapi-uvicorn-sync",
            "fastapi-gunicorn": "fastapi-gunicorn",
            "fastapi-gunicorn-sync": "fastapi-gunicorn-sync",
        }
        framework = framework_name_map.get(service, service.capitalize())
        base_url = FRAMEWORKS.get(framework)

        if not base_url:
            print(f"⚠️ Skipping {framework}: No base URL configured.")
            stop_and_remove_service(service)
            continue

        if not wait_for_service_ready(base_url):
            print(f"⚠️ Skipping {framework} because it failed the health check.")
            stop_and_remove_service(service)
            continue

        for case in TEST_CASES:
            print(f"  -> Running test: {case['name']}")
            url = base_url.rstrip("/") + case["path"]
            lua_script = None
            if case["method"] in ["POST", "PUT", "DELETE"]:
                lua_script = write_lua_script(
                    LUA_TEMPLATES[case["method"]],
                    f"{case['method'].lower()}_{framework}",
                )
                if case["method"] == "DELETE":
                    url = base_url  # Path is in Lua script

            output = run_wrk(url, DURATION, CONCURRENCY, THREADS, lua_script)
            parsed = parse_wrk_output(output)

            if parsed:
                results.append(
                    {
                        "framework": framework,
                        "test": case["name"],
                        "requests_per_sec": parsed.get("requests_per_sec"),
                        "avg_latency_ms": parsed.get("avg_latency_ms"),
                        "total_requests": int(
                            parsed.get("requests_per_sec") * int(DURATION)
                        ),
                    }
                )

        stop_and_remove_service(service)
        time.sleep(2)

    # Stop all containers at the end
    stop_and_remove_all_services()

    if results:
        with open(OUTPUT_PATH, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)

    print(f"\n✅ Benchmarking complete. Results saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
