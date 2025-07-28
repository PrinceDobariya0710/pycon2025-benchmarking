# 🔬 Benchmarking Strategy

This project benchmarks various web frameworks (FastAPI, Django, Flask, Gin, ExpressJS) across multiple real-world API scenarios. The goal is to provide fair, reproducible, and meaningful comparisons of performance.

---

## 📌 Benchmarking Plan

### 🔄 Test Categories

| Test Name         | Description                                                                 | DB Required |
|------------------|-----------------------------------------------------------------------------|-------------|
| PlainText         | Simple `GET /ping` returning "Hello World"                                 | ❌ No        |
| JSON Echo         | `POST /echo` that returns the posted JSON                                  | ❌ No        |
| Create Product    | `POST /products` to create new product records                             | ⚠️ Optional |
| Get Product       | `GET /products/{id}` retrieves a product by ID                             | ✅ Yes       |
| List Products     | `GET /products` returns filtered or paginated product lists                | ✅ Yes       |
| Update Product    | `PUT /products/{id}` updates an existing product                           | ✅ Yes       |
| Fortune 100       | `GET /fortune` renders top 100 products as HTML                            | ✅ Yes       |
| Delete Products   | `DELETE` a range of products (up to 10,000)                                | ✅ Yes       |

---

## 🧪 Execution Strategy

### ✅ Recommended Flow

1. **Preload database** with 10,000 products using the provided CSV dataset.
2. Run **PlainText**, **JSON**, and **Create Product** benchmarks.
3. Optionally reset database (to restore 10,000 products).
4. Run **Get**, **List**, **Update**, and **Fortune 100** benchmarks.
5. Run **Delete Product** benchmark **last**.
6. Re-seed database if you want to re-run benchmarks for consistency.

---

## ⚙️ How to Preload Database

### 1. Python Seeding Script (Recommended)
Use the provided script to read from `products.csv` and insert into DB using each framework’s ORM.
