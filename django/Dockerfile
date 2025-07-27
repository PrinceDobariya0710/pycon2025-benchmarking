FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install --upgrade pip && pip install -r requirements.txt
EXPOSE 8002
CMD ["gunicorn", "--bind", "0.0.0.0:8002", "core.wsgi:application", "--workers", "1"]
# Replace django_project with your actual Django project name
