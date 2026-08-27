FROM python:3.11-slim
WORKDIR /app
RUN pip install fastapi uvicorn httpx
COPY minimal_app.py .
CMD ["sh", "-c", "python -m uvicorn minimal_app:app --host 0.0.0.0 --port ${PORT:-8000}"]
