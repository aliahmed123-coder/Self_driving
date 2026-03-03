# Electric Vehicle Software MVP Plan (90 Days)

## Product Direction
Do **not** build a full EV operating system for the MVP.

Build a **high-impact software layer** on top of existing vehicle platforms to prove customer value fast.

## MVP Wedge
**Smart Charging + Battery Health Intelligence** for EV fleets.

### Core Value Proposition
- Reduce charging cost.
- Improve vehicle uptime.
- Slow battery degradation through charging strategy recommendations.

## Target User
- Fleet operations manager (delivery, ride-hail, service fleets).
- Secondary: dispatcher and maintenance lead.

## MVP Scope (Must-Have)
1. **Data Ingestion**
   - Pull telemetry from existing APIs/telematics providers.
   - Normalize state-of-charge (SoC), charging sessions, trip energy use.
2. **Charging Optimization**
   - Recommend best charging windows based on tariff/time-of-use data.
   - Basic scheduling recommendations by vehicle and depot.
3. **Battery Health Signals**
   - Simple degradation-risk score using charging patterns and temperature exposure.
4. **Ops Dashboard**
   - Fleet overview: SoC, next-charge recommendation, exception alerts.
5. **Reporting**
   - Weekly KPI report: charging spend, missed departures, battery-risk trend.

## Non-Goals (for MVP)
- No custom kernel/driver work.
- No on-vehicle real-time control loops.
- No full digital twin.
- No broad multi-region compliance automation.

## Architecture (MVP)
- **Ingestion service**: receives telematics + utility/tariff feeds.
- **Processing jobs**: compute recommendations and health scores daily/hourly.
- **API layer**: serves fleet and vehicle-level insights.
- **Web dashboard**: operations UI for recommendations and alerts.
- **Audit/logging**: basic traceability for recommendations.

## 90-Day Timeline

### Phase 1 (Days 1–30): Foundation
- Confirm design partners (2–3 fleets).
- Define required data contracts.
- Implement ingestion pipeline for one telematics source.
- Build baseline dashboard shell.

### Phase 2 (Days 31–60): Intelligence
- Ship charging recommendation engine v1.
- Add battery risk scoring v1.
- Add alerting for low-SoC and charging anomalies.

### Phase 3 (Days 61–90): Pilot + Proof
- Run pilot with real fleet data.
- Track KPI deltas against baseline.
- Produce ROI summary and conversion package for paid rollout.

## Success Metrics
- **8–15% reduction** in charging energy cost.
- **20% fewer** missed-charge events.
- **Measurable reduction** in high-risk charging behaviors.
- Weekly active usage from fleet operations users.

## Risks and Mitigations
- **Data quality gaps** → add validation and fallback heuristics.
- **Integration delays** → start with one provider and one depot first.
- **Change management** → include explainability in recommendations.

## Next Decision Gate
At day 90, decide whether to:
1. Expand integrations and geographies.
2. Add advanced predictive maintenance.
3. Add constrained optimization (route + charging + tariff).

Only after strong commercial proof should you consider deeper platform work.
