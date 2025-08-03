wrk.method = "POST"
wrk.headers["Content-Type"] = "application/json"
wrk.body = '{"name":"Test Product","price":99.99,"stock":100, "description": "desc", "brand": "brand", "category": "cat", "currency": "USD", "ean": "123", "color": "red", "size": "M", "availability": "in-stock", "internal_id": "123"}'