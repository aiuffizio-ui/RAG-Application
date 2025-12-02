FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Create data dir
RUN mkdir -p /data

ENV PYTHONPATH=/app
ENV DATA_DIR=/data

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
