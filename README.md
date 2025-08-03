# 🚀 Framework Performance Benchmarking

A comprehensive benchmarking suite comparing popular web frameworks (FastAPI, Django, Flask, Gin, ExpressJS) across real-world API scenarios. This project provides reproducible performance metrics using Docker containers and WRK for load testing.

## 🎯 Frameworks Tested
- FastAPI (Python, async)
- FastAPI Sync (Python, sync)
- Django (Python)
- Flask (Python)
- Gin (Go)
- Express (Node.js)

## 🔍 Benchmark Categories

| Endpoint          | Method | Path           | Description                                    | DB Required |
|------------------|--------|----------------|------------------------------------------------|------------|
| Plain Text       | GET    | `/plain-text`  | Returns "Hello World" - baseline performance   | ❌ No       |
| JSON Response    | GET    | `/json`        | Returns simple JSON object                     | ❌ No       |
| Create Product   | POST   | `/products`    | Creates new product with validation            | ✅ Yes      |
| Get Product      | GET    | `/products/id` | Retrieves single product from database         | ✅ Yes      |
| List Products    | GET    | `/products`    | Returns paginated product list                 | ✅ Yes      |
| Update Product   | PUT    | `/products/id` | Updates existing product                       | ✅ Yes      |
| Delete Product   | DELETE | `/products/id` | Removes product from database                  | ✅ Yes      |
| Fortune 100      | GET    | `/fortune`     | Returns HTML table of 100 products            | ✅ Yes      |

## 🛠️ Setup & Installation

1. **Clone Repository**
   ```bash
   git clone https://github.com/PrinceDobariya0710/pycon2025-benchmarking.git
   cd pycon2025-benchmarking
   ```

2. **Install UV Package Manager**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Environment Setup**
   ```bash
   # Use example env file
   .docker.env
   
   # Review and modify environment variables if needed
   ```

4. **Build Docker Images**
   ```bash
   docker compose -f docker-compose.benchmark.yml build
   ```

5. **Install Dependencies**
   ```bash
   uv sync
   ```

## 🏃‍♂️ Running Benchmarks

```bash
uv run benchmark_wrk.py
```

The benchmark runner will:
1. Start PostgreSQL container
2. Seed database with sample product data
3. Start each framework's container
4. Run WRK benchmarks for each endpoint
5. Save results to CSV files in `results/` directory

## 📊 Benchmark Configuration

- **Duration**: 60 seconds per test
- **Connections**: 10 concurrent connections
- **Threads**: 2 threads for WRK
- **Database**: PostgreSQL with 10,000 pre-loaded products

## 🔧 Framework Implementation Details

Each framework implements identical endpoints with the same functionality:

```python
# Example Product Model
{
    "id": int,
    "name": str,
    "description": str,
    "price": float,
    "stock": int,
    "brand": str,
    "category": str,
    "currency": str,
    "ean": str,
    "color": str,
    "size": str,
    "availability": str,
    "internal_id": str
}
```

## 📁 Project Structure
```
├── benchmark_wrk.py          # Main benchmark runner
├── docker-compose.yml        # Development compose file
├── docker-compose.benchmark.yml  # Benchmark compose file
├── results/                  # Benchmark results
├── data/                     # Sample data for seeding
├── fastapi/                  # FastAPI implementation
├── django/                   # Django implementation
├── flask/                    # Flask implementation
├── gin/                      # Gin implementation
└── express/                  # Express.js implementation
```

## 🤝 Contributing

Contributions are welcome! Feel free to:

- Open issues for bugs or suggestions
- Submit PRs for improvements
- Add new frameworks for comparison
- Suggest new benchmark scenarios

### Contributing Guidelines
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📝 Notes

- All frameworks use similar database schemas and API contracts
- Each implementation follows framework best practices
- Tests run in isolated Docker containers for consistency
- Results may vary based on hardware and network conditions

## ⚖️ License

MIT License - feel free to use and modify for your own benchmarking needs.