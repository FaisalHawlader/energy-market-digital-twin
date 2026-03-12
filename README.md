# Industrial Energy Market Digital Twin Prototype

A real-time, event-driven digital twin prototype for simulating,
monitoring, and forecasting electricity market conditions.

This project demonstrates an end-to-end systems engineering approach
using a multi-service architecture with Kafka, FastAPI, Streamlit, and
Docker. It is designed as a portfolio-quality prototype to showcase how
a digital twin platform can be built for energy market monitoring and
operational decision support.

------------------------------------------------------------------------

# Overview

The system simulates an electricity market environment and streams
synthetic grid states through Kafka. A backend digital twin service
consumes these events, maintains the current system state, generates
forecasts and alerts, and exposes APIs for downstream applications.

A Streamlit dashboard provides a live operational view of the simulated
system.

The simulation includes:

-   electricity demand
-   solar generation
-   wind generation
-   conventional generation
-   battery storage behavior
-   interconnector imports
-   reserve margin and imbalance
-   electricity price
-   carbon intensity
-   renewable share
-   grid operational status

------------------------------------------------------------------------

# Key Features

-   Real-time energy market simulation
-   Kafka-based event streaming architecture
-   FastAPI backend serving digital twin state
-   Historical state tracking
-   Short-horizon forecasting
-   Automated alert generation
-   Streamlit + Plotly operational dashboard
-   Dockerized multi-service deployment
-   Modular architecture designed for future expansion

------------------------------------------------------------------------

# System Architecture

Simulator → Kafka Topic (energy.market.states) → FastAPI Digital Twin
Backend → Streamlit Dashboard

Future extensions may include optimization services, historian
databases, anomaly detection systems, and external integrations.

------------------------------------------------------------------------

# Services

## kafka

Kafka acts as the event streaming backbone of the system. All simulated
market states are published to the topic:

energy.market.states

This allows other services to subscribe to the stream without modifying
the simulator.

## simulator

The simulator generates synthetic electricity market states and
publishes them to Kafka.

Each event includes: - timestamp - renewable generation - conventional
generation - system demand - battery level - electricity price - carbon
intensity - renewable share - grid status

## api

The FastAPI backend functions as the digital twin service. It:

-   consumes Kafka events
-   maintains system state history
-   generates forecasts
-   produces alerts
-   exposes REST and WebSocket APIs

## dashboard

The Streamlit dashboard visualizes:

-   live grid state
-   historical trends
-   renewable share
-   price dynamics
-   alerts
-   forecasts

------------------------------------------------------------------------

# Repository Structure

. ├── docker-compose.yml ├── README.md └── services ├── api ├──
dashboard ├── simulator └── shared

------------------------------------------------------------------------

# Quick Start

## Prerequisites

Install:

-   Docker
-   Docker Compose

## Run the platform

docker compose up --build

This starts:

-   Kafka broker
-   simulator
-   API service
-   dashboard

------------------------------------------------------------------------

# Access the Platform

API docs: http://localhost:8000/docs

Dashboard: http://localhost:8501

------------------------------------------------------------------------

# API Endpoints

GET /api/health\
GET /api/state\
GET /api/history?points=120\
GET /api/forecast?horizon=20\
GET /api/alerts?limit=10\
WS /ws/state

------------------------------------------------------------------------

# Example Use Cases

This prototype demonstrates:

-   digital twin platforms
-   energy system monitoring
-   real-time streaming pipelines
-   event-driven architecture
-   operational dashboards
-   forecasting and alert systems

------------------------------------------------------------------------

# Why This Project Matters

Many projects focus only on data analysis notebooks. This project
demonstrates full system design by integrating:

-   simulation
-   streaming infrastructure
-   backend services
-   forecasting
-   alerts
-   visualization

It highlights how a digital twin platform can be designed using modern
distributed system architecture.

------------------------------------------------------------------------

# Current Limitations

This is a demonstration prototype:

-   synthetic data only
-   simple forecasting logic
-   no persistent database yet
-   static alert thresholds
-   not production hardened

------------------------------------------------------------------------

# Possible Extensions

Future improvements could include:

-   PostgreSQL or TimescaleDB historian
-   Grafana monitoring
-   machine learning forecasting
-   reinforcement learning battery optimization
-   anomaly detection services
-   real electricity market data
-   Kubernetes deployment

------------------------------------------------------------------------

# Example Project Description

Built a real-time energy market digital twin prototype using Kafka,
FastAPI, Streamlit, and Docker to simulate, monitor, and forecast
electricity system conditions through an event-driven multi-service
architecture.

------------------------------------------------------------------------

# License

Provided for demonstration and educational purposes.
