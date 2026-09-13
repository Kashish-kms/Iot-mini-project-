# Privacy-aware sensor simulator.
# Publishes ONLY 1-minute-window aggregated telemetry over TLS MQTT.
FROM python:3.11-slim

WORKDIR /app

# MQTT broker CA is mounted into this path by docker-compose.
RUN mkdir -p /etc/ssl/certs && mkdir -p /app/simulator

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY simulator/__init__.py /app/simulator/__init__.py
COPY simulator/config.py    /app/simulator/config.py
COPY simulator/generator.py /app/simulator/generator.py
COPY simulator/publisher.py /app/simulator/publisher.py

# Unbuffered stdout so docker-compose logs work live.
ENV PYTHONUNBUFFERED=1
# Use simulator MQTT creds role.
ENV MQTT_USERNAME=sim_user
ENV MQTT_PASSWORD=sim_pass
ENV SIM_REALTIME=1

CMD ["python", "-u", "-m", "simulator.publisher"]
