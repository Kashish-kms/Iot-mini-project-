# Streamlit live dashboard.
FROM python:3.11-slim

WORKDIR /app

RUN mkdir -p /data /app/dashboard /app/ingestion /app/ml/models /app/simulator

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Dashboard itself.
COPY dashboard/__init__.py    /app/dashboard/__init__.py
COPY dashboard/components.py  /app/dashboard/components.py
COPY dashboard/app.py         /app/dashboard/app.py

# Shared modules we import (ingestion.db, ml.train features).
COPY ingestion/__init__.py    /app/ingestion/__init__.py
COPY ingestion/database.py    /app/ingestion/database.py
COPY ingestion/preprocessing.py /app/ingestion/preprocessing.py

COPY simulator/__init__.py    /app/simulator/__init__.py
COPY simulator/config.py      /app/simulator/config.py
COPY simulator/generator.py   /app/simulator/generator.py

COPY ml/__init__.py           /app/ml/__init__.py
COPY ml/train.py              /app/ml/train.py
# Models dir (volume mount or pre-trained COPY).
VOLUME ["/app/ml/models"]

ENV PYTHONUNBUFFERED=1
ENV DB_PATH=/data/iot.db
ENV REFRESH_SEC=10
ENV DASH_WINDOW_MIN=60

EXPOSE 8501
HEALTHCHECK CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8501/_stcore/health', timeout=5).read().find(b'ok')>=0 else 1)" 2>/dev/null || true

CMD ["streamlit", "run", "/app/dashboard/app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--browser.gatherUsageStats=false", \
     "--global.developmentMode=false"]
