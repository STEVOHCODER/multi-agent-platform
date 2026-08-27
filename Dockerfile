FROM python:3.11-slim
WORKDIR /app
COPY saas/backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY saas/backend/ .
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
