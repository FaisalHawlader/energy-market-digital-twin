# Industrial Energy Market Digital Twin Prototype

A polished end-to-end prototype that demonstrates **Role 3 / end-to-end systems engineering** for an energy-market-focused digital twin.

## What this prototype shows

- **Real-time simulation** of supply, demand, battery, carbon intensity, and price events
- **Kafka-based streaming backbone** for event-driven architecture
- **FastAPI digital twin backend** consuming market events and exposing APIs + WebSocket
- **Industrial-style dashboard** built with Streamlit + Plotly
- **Dockerized deployment** with `docker compose`

## Architecture

```text
Simulator --> Kafka topic (energy.market.states) --> FastAPI Digital Twin API --> Streamlit Dashboard
                                                                               +--> future consumers (optimizer, alerting, historian)
```

## Services

- `kafka`: Kafka broker in KRaft mode
- `simulator`: publishes synthetic market states every second
- `api`: consumes Kafka events, builds the latest digital twin state, serves APIs
- `dashboard`: industrial UI consuming the API

## Quick start

```bash
docker compose up --build
```

Then open:

- API docs: `http://localhost:8000/docs`
- Dashboard: `http://localhost:8501`

## Main API endpoints

- `GET /api/health`
- `GET /api/state`
- `GET /api/history?points=120`
- `GET /api/forecast?horizon=20`
- `GET /api/alerts`
- `WS  /ws/state`

## Why this is good for your LIST discussion

This prototype demonstrates that you can:

1. design a **multi-service system** rather than a notebook-only demo
2. use **message-driven architecture** with Kafka
3. integrate **simulation, backend, forecasting, and UI**
4. build something that looks closer to a **platform** than a research script


## Notes

- This is a **dummy-data prototype** intended for demonstration.
- It is intentionally structured so future extensions are easy, such as:
  - RL-based battery dispatch
  - anomaly detection microservice
  - PostgreSQL/Timescale historian
  - Grafana observability
  - Kubernetes deployment
