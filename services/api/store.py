from __future__ import annotations

from collections import deque
from threading import Lock

from shared.models import AlertEvent, EnergyMarketState

class TwinStore:
    def __init__(self, max_points: int = 2000, max_alerts: int = 200) -> None:
        self._history: deque[EnergyMarketState] = deque(maxlen=max_points)
        self._alerts: deque[AlertEvent] = deque(maxlen=max_alerts)
        self._lock = Lock()

    def append_state(self, state: EnergyMarketState) -> None:
        with self._lock:
            self._history.append(state)

    def append_alert(self, alert: AlertEvent) -> None:
        with self._lock:
            self._alerts.appendleft(alert)

    def latest(self) -> EnergyMarketState | None:
        with self._lock:
            return self._history[-1] if self._history else None

    def history(self, points: int) -> list[EnergyMarketState]:
        with self._lock:
            return list(self._history)[-points:]

    def alerts(self, limit: int = 20) -> list[AlertEvent]:
        with self._lock:
            return list(self._alerts)[:limit]
