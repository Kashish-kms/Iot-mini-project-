import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .database import init_db
from .mqtt_service import mqtt_service
from .websocket_hub import ws_hub

# Route imports
from .routes.auth_routes import router as auth_router
from .routes.readings_routes import router as readings_router
from .routes.model_routes import router as model_router
from .routes.eda_routes import router as eda_router
from .routes.device_routes import router as device_router
from .routes.alerts_routes import router as alerts_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("[VeilSense] Initializing database...")
    init_db()
    loop = asyncio.get_running_loop()
    print("[VeilSense] Starting MQTT / Telemetry streaming services...")
    mqtt_service.start(event_loop=loop)
    yield
    # Shutdown
    print("[VeilSense] Shutting down services.")

app = FastAPI(
    title="VeilSense API",
    description="Privacy-aware intelligent smart IoT monitoring platform backend",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(auth_router)
app.include_router(readings_router)
app.include_router(model_router)
app.include_router(eda_router)
app.include_router(device_router)
app.include_router(alerts_router)

@app.get("/")
def root():
    return {
        "service": "VeilSense Backend",
        "tagline": "Intelligence without intrusion.",
        "status": "operational",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "mqtt_connected": mqtt_service.is_connected,
        "device_online": mqtt_service.latest_status["online"],
        "fan_state": mqtt_service.fan_state
    }

@app.websocket("/ws/live")
async def websocket_live_stream(websocket: WebSocket):
    await ws_hub.connect(websocket)
    try:
        while True:
            # Keep-alive or handle incoming client pings
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text('{"type": "pong"}')
    except WebSocketDisconnect:
        ws_hub.disconnect(websocket)
    except Exception:
        ws_hub.disconnect(websocket)
