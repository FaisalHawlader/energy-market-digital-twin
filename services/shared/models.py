from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

GridStatus = Literal["Stable", "Watch", "Critical"]
BatteryMode = Literal["charge", "discharge", "idle"]

class EnergyMarketState(BaseModel):
    timestamp: datetime
    solar_mw: float = Field(ge=0)
    wind_mw: float = Field(ge=0)
    conventional_mw: float = Field(ge=0)
    demand_mw: float = Field(ge=0)
    interconnector_import_mw: float
    battery_level_pct: float = Field(ge=0, le=100)
    battery_power_mw: float
    battery_mode: BatteryMode
    reserve_margin_mw: float
    imbalance_mw: float = Field(ge=0)
    market_price_eur_mwh: float = Field(ge=0)
    carbon_intensity_gco2_kwh: float = Field(ge=0)
    renewable_share_pct: float = Field(ge=0, le=100)
    grid_status: GridStatus
    alert_flag: bool = False

class ForecastPoint(BaseModel):
    timestamp: datetime
    predicted_demand_mw: float
    predicted_price_eur_mwh: float
    predicted_renewable_share_pct: float

class ForecastResponse(BaseModel):
    generated_at: datetime
    horizon_minutes: int
    recommendation: str
    reasoning: str
    points: list[ForecastPoint]

class AlertEvent(BaseModel):
    timestamp: datetime
    severity: Literal["info", "warning", "critical"]
    title: str
    message: str
