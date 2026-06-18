# KMIA_NDFD_Year_MaxT_Precision_2023

- Target dates analyzed: **365**
- Forecast releases (0–36h before 4 PM ET): **13455**
- Overall MAE: **1.30°F**
- Overall within 2°F: **73.4%**

## 1. Lead-time accuracy (hours before 4 PM ET anchor)

- **10h lead**: 76.2% within 2°F (MAE 1.29°F, n=362)
- **0h lead**: 75.9% within 2°F (MAE 1.20°F, n=365)
- **11h lead**: 75.8% within 2°F (MAE 1.27°F, n=363)
- **1h lead**: 75.3% within 2°F (MAE 1.23°F, n=365)
- **12h lead**: 75.1% within 2°F (MAE 1.28°F, n=362)

Median best lead hour per day: **33.0h** before anchor.

## 2. Weather-condition accuracy

- Best **forecast_stability** = **STABLE**: 77.2% within 2°F (n=6475)
- Best **observed_wdir_cardinal** = **SE**: 81.9% within 2°F (n=3247)
- Best **forecast_wdir_cardinal** = **W**: 77.5% within 2°F (n=621)
- Best **range_bucket** = **narrow_<=1.5F**: 75.4% within 2°F (n=8283)

## 3. Seasonal accuracy

- Month **8**: 86.9% within 2°F (MAE 1.07°F)
- Month **7**: 79.1% within 2°F (MAE 1.06°F)
- Month **9**: 77.6% within 2°F (MAE 1.27°F)
- Month **5**: 76.9% within 2°F (MAE 1.08°F)
- Worst month **4**: 66.4% within 2°F

**Why seasons differ (Miami):** Winter dry-season days with steady easterly flow tend toward STABLE forecasts; summer convective afternoons and sea-breeze timing shift observed max earlier/later and widen forecast spread (UNSTABLE), lowering hit rate.
