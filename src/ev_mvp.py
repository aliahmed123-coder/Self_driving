"""Core EV fleet MVP logic.

This module provides a minimal implementation for:
- charging window recommendations based on time-of-use tariff periods
- battery risk scoring from charging behavior and thermal exposure
- weekly KPI rollups for fleet operations
"""

from dataclasses import dataclass
from typing import Iterable, List, Optional


@dataclass(frozen=True)
class TariffWindow:
    """Represents a tariff period in 24-hour local time."""

    start_hour: int
    end_hour: int
    price_per_kwh: float

    def contains(self, hour: int) -> bool:
        """Return True if an hour belongs to this window.

        Supports both normal ranges (e.g. 6-20) and overnight ranges (e.g. 22-6).
        """
        if not (0 <= hour <= 23):
            raise ValueError("hour must be in [0, 23]")

        if self.start_hour <= self.end_hour:
            return self.start_hour <= hour < self.end_hour
        return hour >= self.start_hour or hour < self.end_hour


@dataclass(frozen=True)
class VehicleState:
    vehicle_id: str
    soc_percent: float
    next_departure_hour: int
    required_soc_percent: float = 80.0


@dataclass(frozen=True)
class ChargingRecommendation:
    vehicle_id: str
    charge_start_hour: int
    charge_end_hour: int
    expected_cost_per_kwh: float
    reason: str


@dataclass(frozen=True)
class WeeklyKPI:
    baseline_cost: float
    optimized_cost: float
    missed_departures_baseline: int
    missed_departures_optimized: int

    @property
    def cost_reduction_percent(self) -> float:
        if self.baseline_cost <= 0:
            return 0.0
        return ((self.baseline_cost - self.optimized_cost) / self.baseline_cost) * 100.0

    @property
    def missed_departure_reduction_percent(self) -> float:
        if self.missed_departures_baseline <= 0:
            return 0.0
        delta = self.missed_departures_baseline - self.missed_departures_optimized
        return (delta / self.missed_departures_baseline) * 100.0


def battery_risk_score(avg_charge_ceiling_percent: float, fast_charge_ratio: float, avg_temp_c: float) -> int:
    """Return a simple 0-100 risk score (higher means worse).

    The scoring heuristic intentionally stays simple for MVP explainability.
    """
    if not (0 <= avg_charge_ceiling_percent <= 100):
        raise ValueError("avg_charge_ceiling_percent must be in [0, 100]")
    if not (0 <= fast_charge_ratio <= 1):
        raise ValueError("fast_charge_ratio must be in [0, 1]")

    score = 0.0

    # Frequent charging near 100% increases degradation risk.
    if avg_charge_ceiling_percent > 90:
        score += (avg_charge_ceiling_percent - 90) * 2.0

    # High fast-charge share can increase battery stress.
    score += fast_charge_ratio * 45.0

    # Elevated thermal conditions are harmful over time.
    if avg_temp_c > 30:
        score += (avg_temp_c - 30) * 1.5

    return int(max(0, min(100, round(score))))


def recommend_charging_window(
    vehicle: VehicleState,
    tariff_windows: Iterable[TariffWindow],
    min_hours_needed: int = 2,
    now_hour: Optional[int] = None,
) -> ChargingRecommendation:
    """Recommend the cheapest feasible charging window before departure.

    Feasibility rule (MVP): choose lowest-cost tariff hour-block of min_hours_needed
    that ends before departure and starts no earlier than current hour.
    """
    if min_hours_needed <= 0:
        raise ValueError("min_hours_needed must be positive")
    if not (0 <= vehicle.next_departure_hour <= 23):
        raise ValueError("vehicle.next_departure_hour must be in [0, 23]")

    current_hour = 0 if now_hour is None else now_hour
    if not (0 <= current_hour <= 23):
        raise ValueError("now_hour must be in [0, 23]")

    hours_until_departure: List[int] = []
    h = current_hour
    while h != vehicle.next_departure_hour:
        hours_until_departure.append(h)
        h = (h + 1) % 24
        if len(hours_until_departure) > 24:
            break

    if len(hours_until_departure) < min_hours_needed:
        raise ValueError("insufficient time before departure for requested charging duration")

    price_by_hour = {hour: _price_at_hour(hour, tariff_windows) for hour in range(24)}

    best_block = None
    best_avg_price = float("inf")

    for idx in range(0, len(hours_until_departure) - min_hours_needed + 1):
        block = hours_until_departure[idx : idx + min_hours_needed]
        avg_price = sum(price_by_hour[h] for h in block) / min_hours_needed
        if avg_price < best_avg_price:
            best_avg_price = avg_price
            best_block = block

    assert best_block is not None
    start_hour = best_block[0]
    end_hour = (best_block[-1] + 1) % 24

    reason = (
        f"Selected lowest-cost {min_hours_needed}h window before departure "
        f"(avg tariff {best_avg_price:.2f}/kWh)."
    )

    return ChargingRecommendation(
        vehicle_id=vehicle.vehicle_id,
        charge_start_hour=start_hour,
        charge_end_hour=end_hour,
        expected_cost_per_kwh=round(best_avg_price, 4),
        reason=reason,
    )


def generate_weekly_kpi(
    baseline_cost: float,
    optimized_cost: float,
    missed_departures_baseline: int,
    missed_departures_optimized: int,
) -> WeeklyKPI:
    if baseline_cost < 0 or optimized_cost < 0:
        raise ValueError("costs must be non-negative")
    if missed_departures_baseline < 0 or missed_departures_optimized < 0:
        raise ValueError("missed departures must be non-negative")

    return WeeklyKPI(
        baseline_cost=baseline_cost,
        optimized_cost=optimized_cost,
        missed_departures_baseline=missed_departures_baseline,
        missed_departures_optimized=missed_departures_optimized,
    )


def _price_at_hour(hour: int, tariff_windows: Iterable[TariffWindow]) -> float:
    matching_prices = [w.price_per_kwh for w in tariff_windows if w.contains(hour)]
    if not matching_prices:
        raise ValueError(f"No tariff defined for hour {hour}")
    return min(matching_prices)
