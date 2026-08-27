FROM python:3.11-slim
WORKDIR /app/saas/backend
COPY saas/backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY saas/backend/ .
EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
