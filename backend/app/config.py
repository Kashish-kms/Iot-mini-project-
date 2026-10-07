import os
from pydantic import BaseModel

class Settings(BaseModel):
    PORT: int = int(os.getenv("PORT", "8000"))
    HOST: str = os.getenv("HOST", "0.0.0.0")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "veilsense_super_secret_jwt_key_2025")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    # MQTT
    MQTT_BROKER_HOST: str = os.getenv("MQTT_BROKER_HOST", "localhost")
    MQTT_BROKER_PORT: int = int(os.getenv("MQTT_BROKER_PORT", "1883")) # Default non-TLS for dev fallback
    MQTT_TLS_PORT: int = int(os.getenv("MQTT_TLS_PORT", "8883"))
    MQTT_USE_TLS: bool = os.getenv("MQTT_USE_TLS", "false").lower() == "true"
    MQTT_USERNAME: str = os.getenv("MQTT_USERNAME", "veilsense_edge")
    MQTT_PASSWORD: str = os.getenv("MQTT_PASSWORD", "edge_secret_2025")
    MQTT_TOPIC_TELEMETRY: str = "veilsense/telemetry/room1"
    MQTT_TOPIC_ACTUATION: str = "veilsense/actuation/fan"
    
    # Database
    BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))
    DB_PATH: str = os.path.join(BASE_DIR, "..", "veilsense.db")

settings = Settings()
