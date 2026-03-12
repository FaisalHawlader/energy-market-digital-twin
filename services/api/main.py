from __future__ import annotations

import json
import os
import threading
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from kafka import KafkaConsumer

from api.predictor import ForecastEngine
from api.store import TwinStore
from shared.models import AlertEvent, EnergyMarketState

class WebSocketHub:
    def __init__(self) -> None:
        self.connections: list[WebSocket] = []
        self.lock = threading.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        with self.lock:
            self.connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        with self.lock:
            if websocket in self.connections:
                self.connections.remove(websocket)

store = TwinStore()
forecast_engine = ForecastEngine()
hub = WebSocketHub()
consumer_started = False

def build_consumer() -> KafkaConsumer:
    bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    topic = os.getenv("KAFKA_TOPIC", "energy.market.states")
    return KafkaConsumer(
        topic,
        bootstrap_servers=bootstrap,
        auto_offset_reset="latest",
        enable_auto_commit=True,
        group_id="energy-market-digital-twin-api",
        value_deserializer=lambda value: json.loads(value.decode("utf-8")),
    )

def maybe_create_alert(state: EnergyMarketState) -> AlertEvent | None:
    if state.grid_status == "Critical":
        return AlertEvent(
            timestamp=state.timestamp,
            severity="critical",
            title="Grid stress event",
            message=f"Critical imbalance detected ({state.imbalance_mw:.1f} MW).",
        )
    if state.market_price_eur_mwh > 120:
        return AlertEvent(
            timestamp=state.timestamp,
            severity="warning",
            title="Price spike",
            message=f"Market price exceeded threshold at €{state.market_price_eur_mwh:.2f}/MWh.",
        )
    if state.carbon_intensity_gco2_kwh > 300:
        return AlertEvent(
            timestamp=state.timestamp,
            severity="warning",
            title="Carbon intensity high",
            message=f"Carbon intensity rose to {state.carbon_intensity_gco2_kwh:.0f} gCO2/kWh.",
        )
    return None

def consume_loop() -> None:
    consumer = build_consumer()
    while True:
        try:
            for message in consumer:
                state = EnergyMarketState.model_validate(message.value)
                store.append_state(state)
                alert = maybe_create_alert(state)
                if alert is not None:
                    store.append_alert(alert)
        except Exception as exc:
            print(f"consumer error: {exc}")
            time.sleep(2)

def start_consumer() -> None:
    global consumer_started
    if consumer_started:
        return
    thread = threading.Thread(target=consume_loop, daemon=True, name="kafka-consumer-thread")
    thread.start()
    consumer_started = True

@asynccontextmanager
async def lifespan(_: FastAPI):
    start_consumer()
    yield

app = FastAPI(
    title="Industrial Energy Market Digital Twin API",
    version="2.0.0",
    description="Kafka-backed digital twin backend for an energy market prototype.",
    lifespan=lifespan,
)

@app.get("/api/health")
def health() -> dict:
    latest = store.latest()
    return {
        "status": "ok",
        "consumer_started": consumer_started,
        "latest_timestamp": latest.timestamp.isoformat() if latest else None,
    }

@app.get("/api/state")
def get_state() -> dict:
    latest = store.latest()
    if latest is None:
        raise HTTPException(status_code=503, detail="No market state available yet.")
    return latest.model_dump(mode="json")

@app.get("/api/history")
def get_history(points: int = Query(default=120, ge=10, le=2000)) -> list[dict]:
    return [item.model_dump(mode="json") for item in store.history(points)]

@app.get("/api/forecast")
def get_forecast(horizon: int = Query(default=20, ge=5, le=60)) -> dict:
    history = store.history(180)
    if len(history) < 5:
        raise HTTPException(status_code=503, detail="Not enough history available for forecasting.")
    return forecast_engine.forecast(history, horizon=horizon).model_dump(mode="json")

@app.get("/api/alerts")
def get_alerts(limit: int = Query(default=10, ge=1, le=100)) -> list[dict]:
    return [item.model_dump(mode="json") for item in store.alerts(limit)]

@app.websocket("/ws/state")
async def ws_state(websocket: WebSocket) -> None:
    await hub.connect(websocket)
    try:
        while True:
            latest = store.latest()
            if latest is not None:
                await websocket.send_json(latest.model_dump(mode="json"))
            await websocket.receive_text()
    except WebSocketDisconnect:
        hub.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", "8000")),
        reload=False,
    )
