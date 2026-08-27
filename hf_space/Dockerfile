FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir PyYAML requests

COPY . .

EXPOSE 7860

CMD ["python", "space_entry.py"]
