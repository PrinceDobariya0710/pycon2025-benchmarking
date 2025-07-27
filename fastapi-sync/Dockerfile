FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install --upgrade pip && pip install -r requirements.txt
EXPOSE 8004
CMD ["fastapi", "run", "main.py", "--host", "0.0.0.0", "--port", "8004"]
