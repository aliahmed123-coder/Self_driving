import unittest

from src.ev_mvp import (
    TariffWindow,
    VehicleState,
    battery_risk_score,
    generate_weekly_kpi,
    recommend_charging_window,
)


class TestEvMvp(unittest.TestCase):
    def setUp(self):
        self.tariffs = [
            TariffWindow(start_hour=0, end_hour=6, price_per_kwh=0.12),
            TariffWindow(start_hour=6, end_hour=22, price_per_kwh=0.30),
            TariffWindow(start_hour=22, end_hour=0, price_per_kwh=0.15),
        ]

    def test_battery_risk_score_increases_with_stress(self):
        low = battery_risk_score(avg_charge_ceiling_percent=80, fast_charge_ratio=0.1, avg_temp_c=24)
        high = battery_risk_score(avg_charge_ceiling_percent=98, fast_charge_ratio=0.8, avg_temp_c=38)
        self.assertLess(low, high)

    def test_recommend_charging_window_prefers_off_peak(self):
        vehicle = VehicleState(vehicle_id="V-100", soc_percent=35, next_departure_hour=8)
        rec = recommend_charging_window(vehicle=vehicle, tariff_windows=self.tariffs, min_hours_needed=2, now_hour=1)
        self.assertEqual(rec.charge_start_hour, 1)
        self.assertEqual(rec.charge_end_hour, 3)
        self.assertLess(rec.expected_cost_per_kwh, 0.30)

    def test_recommend_charging_window_handles_overnight_departure(self):
        vehicle = VehicleState(vehicle_id="V-200", soc_percent=40, next_departure_hour=3)
        rec = recommend_charging_window(vehicle=vehicle, tariff_windows=self.tariffs, min_hours_needed=2, now_hour=21)
        self.assertEqual(rec.charge_start_hour, 0)
        self.assertEqual(rec.charge_end_hour, 2)

    def test_generate_weekly_kpi_percentages(self):
        kpi = generate_weekly_kpi(
            baseline_cost=1000,
            optimized_cost=850,
            missed_departures_baseline=20,
            missed_departures_optimized=12,
        )
        self.assertAlmostEqual(kpi.cost_reduction_percent, 15.0)
        self.assertAlmostEqual(kpi.missed_departure_reduction_percent, 40.0)


if __name__ == "__main__":
    unittest.main()
