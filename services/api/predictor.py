from __future__ import annotations

from datetime import timedelta

from shared.models import EnergyMarketState, ForecastPoint, ForecastResponse

class ForecastEngine:
    def forecast(self, history: list[EnergyMarketState], horizon: int = 20) -> ForecastResponse:
        latest = history[-1]
        window = history[-12:] if len(history) >= 12 else history

        avg_demand = sum(item.demand_mw for item in window) / len(window)
        avg_price = sum(item.market_price_eur_mwh for item in window) / len(window)
        avg_renewable = sum(item.renewable_share_pct for item in window) / len(window)

        demand_trend = 0.0
        price_trend = 0.0
        renewable_trend = 0.0
        if len(window) >= 2:
            demand_trend = (window[-1].demand_mw - window[0].demand_mw) / max(1, len(window) - 1)
            price_trend = (window[-1].market_price_eur_mwh - window[0].market_price_eur_mwh) / max(1, len(window) - 1)
            renewable_trend = (window[-1].renewable_share_pct - window[0].renewable_share_pct) / max(1, len(window) - 1)

        points: list[ForecastPoint] = []
        for step in range(1, horizon + 1):
            ts = latest.timestamp + timedelta(minutes=step)
            predicted_demand = max(350.0, avg_demand + demand_trend * step)
            predicted_price = max(20.0, avg_price + price_trend * step + max(0, predicted_demand - avg_demand) * 0.03)
            predicted_renewable_share = min(100.0, max(5.0, avg_renewable + renewable_trend * step))
            points.append(
                ForecastPoint(
                    timestamp=ts,
                    predicted_demand_mw=round(predicted_demand, 2),
                    predicted_price_eur_mwh=round(predicted_price, 2),
                    predicted_renewable_share_pct=round(predicted_renewable_share, 2),
                )
            )

        avg_future_price = sum(point.predicted_price_eur_mwh for point in points) / len(points)
        avg_future_renewable = sum(point.predicted_renewable_share_pct for point in points) / len(points)
        if avg_future_price > 105:
            recommendation = "Preserve battery reserves and reduce non-critical demand exposure"
            reasoning = "Forecast indicates elevated price pressure over the next horizon."
        elif avg_future_renewable > 62:
            recommendation = "Charge storage and increase flexible load absorption"
            reasoning = "Forecast suggests strong renewable availability and favorable flexibility conditions."
        else:
            recommendation = "Operate in balanced mode with standard reserve management"
            reasoning = "No major stress signal is forecast in price or renewable availability."

        return ForecastResponse(
            generated_at=latest.timestamp,
            horizon_minutes=horizon,
            recommendation=recommendation,
            reasoning=reasoning,
            points=points,
        )
