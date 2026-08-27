FROM python:3.11-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=5300
EXPOSE 5300

# app_entry.py starts the FastAPI health-check server (bound to Railway's
# expected port) and runs the real MailPilot agent (EmailWhatsAppAgent,
# main.py -> agent.watch()) continuously in a background thread.
CMD ["sh", "-c", "python -m uvicorn app_entry:app --host 0.0.0.0 --port ${PORT:-5300}"]
