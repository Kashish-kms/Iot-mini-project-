# MQTT -> SQLite ingestion service.
FROM python:3.11-slim

WORKDIR /app

# Shared SQLite volume.
RUN mkdir -p /data /app/ingestion /broker/certs

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY ingestion/__init__.py     /app/ingestion/__init__.py
COPY ingestion/database.py     /app/ingestion/database.py
COPY ingestion/preprocessing.py /app/ingestion/preprocessing.py
COPY ingestion/service.py      /app/ingestion/service.py

ENV PYTHONUNBUFFERED=1
ENV DB_PATH=/data/iot.db
ENV MQTT_INGEST_USERNAME=ingest_user
ENV MQTT_INGEST_PASSWORD=ingest_pass
ENV PREPROCESS_INTERVAL_SEC=120

CMD ["python", "-u", "-m", "ingestion.service"]
