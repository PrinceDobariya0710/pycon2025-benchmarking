FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install --upgrade pip && pip install -r requirements.txt
EXPOSE 8002
CMD ["gunicorn", "--bind", "0.0.0.0:8002", "core.wsgi:application", "--workers", "1"]
# Uncomment the following line to enable access and error logging
# CMD ["gunicorn", "--bind", "0.0.0.0:8002", "core.wsgi:application", "--workers", "1", "--access-logfile", "-", "--error-logfile", "-"]
