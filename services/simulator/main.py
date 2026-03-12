from __future__ import annotations

import json
import math
import os
import random
import time
from datetime import datetime, timedelta

from kafka import KafkaProducer

from shared.models import EnergyMarketState

class MarketSimulator:
    def __init__(self) -> None:
        self.current_time = datetime.now().replace(microsecond=0)
        self.battery_level_pct = 58.0
        self.last_price = 71.0
        self.rng = random.Random(7)

    def _solar(self, minute_of_day: int) -> float:
        peak = 13 * 60
        spread = 220
        x = (minute_of_day - peak) / spread
        cloud_factor = 0.92 + 0.12 * self.rng.random()
        return max(0.0, 650.0 * math.exp(-(x**2)) * cloud_factor)

    def _wind(self, minute_of_day: int) -> float:
        base = 220 + 70 * math.sin(2 * math.pi * minute_of_day / 1440 + 1.3)
        gust = self.rng.uniform(-30, 35)
        return max(50.0, base + gust)

    def _demand(self, minute_of_day: int) -> float:
        morning = 120 * math.exp(-((minute_of_day - 8 * 60) / 110) ** 2)
        evening = 200 * math.exp(-((minute_of_day - 19 * 60) / 150) ** 2)
        industrial = 80 * math.exp(-((minute_of_day - 13 * 60) / 260) ** 2)
        baseline = 640 + 35 * math.sin(2 * math.pi * (minute_of_day - 180) / 1440)
        noise = self.rng.uniform(-22, 22)
        return max(420.0, baseline + morning + evening + industrial + noise)

    def next_state(self) -> EnergyMarketState:
        self.current_time += timedelta(minutes=1)
        minute = self.current_time.hour * 60 + self.current_time.minute

        solar = round(self._solar(minute), 2)
        wind = round(self._wind(minute), 2)
        demand = round(self._demand(minute), 2)

        renewable_total = solar + wind
        conventional_needed = max(0.0, demand - renewable_total)
        conventional = round(min(500.0, conventional_needed + self.rng.uniform(-15, 20)), 2)

        interconnector_import = 0.0
        pre_battery_balance = renewable_total + conventional - demand

        if pre_battery_balance > 30 and self.battery_level_pct < 96:
            battery_power = round(min(60.0, pre_battery_balance * 0.65), 2)
            battery_mode = "charge"
            self.battery_level_pct = min(100.0, self.battery_level_pct + battery_power / 18)
        elif pre_battery_balance < -30 and self.battery_level_pct > 10:
            battery_power = round(max(-60.0, pre_battery_balance * 0.55), 2)
            battery_mode = "discharge"
            self.battery_level_pct = max(0.0, self.battery_level_pct + battery_power / 18)
        else:
            battery_power = 0.0
            battery_mode = "idle"

        post_battery_balance = renewable_total + conventional - demand - battery_power
        if post_battery_balance < -20:
            interconnector_import = round(abs(post_battery_balance) * 0.85, 2)

        reserve_margin = round(max(0.0, renewable_total + conventional + interconnector_import - demand), 2)
        imbalance = round(abs(renewable_total + conventional + interconnector_import - demand - battery_power), 2)

        scarcity = max(0.0, demand - (renewable_total + conventional + interconnector_import))
        oversupply = max(0.0, (renewable_total + conventional) - demand)
        ramping_cost = max(0.0, conventional - 300) * 0.035
        price_delta = 0.038 * scarcity - 0.012 * oversupply + ramping_cost + self.rng.uniform(-1.1, 1.1)
        self.last_price = max(22.0, min(260.0, self.last_price + price_delta))
        price = round(self.last_price, 2)

        renewable_share = round(min(100.0, max(0.0, 100 * renewable_total / max(demand, 1))), 2)
        carbon_intensity = round(max(45.0, 420 - 2.4 * renewable_share + 0.12 * conventional + self.rng.uniform(-6, 6)), 2)

        if imbalance < 15 and reserve_margin > 25:
            status = "Stable"
        elif imbalance < 45:
            status = "Watch"
        else:
            status = "Critical"

        alert_flag = status != "Stable" or price > 120 or carbon_intensity > 300

        return EnergyMarketState(
            timestamp=self.current_time,
            solar_mw=solar,
            wind_mw=wind,
            conventional_mw=conventional,
            demand_mw=demand,
            interconnector_import_mw=interconnector_import,
            battery_level_pct=round(self.battery_level_pct, 2),
            battery_power_mw=battery_power,
            battery_mode=battery_mode,
            reserve_margin_mw=reserve_margin,
            imbalance_mw=imbalance,
            market_price_eur_mwh=price,
            carbon_intensity_gco2_kwh=carbon_intensity,
            renewable_share_pct=renewable_share,
            grid_status=status,
            alert_flag=alert_flag,
        )

def build_producer(bootstrap_servers: str) -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=bootstrap_servers,
        value_serializer=lambda value: json.dumps(value).encode("utf-8"),
        key_serializer=lambda value: value.encode("utf-8"),
    )

def main() -> None:
    bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    topic = os.getenv("KAFKA_TOPIC", "energy.market.states")
    interval = float(os.getenv("PUBLISH_INTERVAL_SECONDS", "1"))

    producer = build_producer(bootstrap)
    simulator = MarketSimulator()

    while True:
        state = simulator.next_state()
        producer.send(topic, key="lux-grid", value=state.model_dump(mode="json"))
        producer.flush()
        print(f"published {state.timestamp.isoformat()} price={state.market_price_eur_mwh} status={state.grid_status}")
        time.sleep(interval)

if __name__ == "__main__":
    main()
