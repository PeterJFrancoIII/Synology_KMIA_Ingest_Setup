# KMIA_NDFD_Year_MaxT_Precision_2024

- Target dates analyzed: **366**
- Forecast releases (0–36h before 4 PM ET): **13490**
- Overall MAE: **1.21°F**
- Overall within 2°F: **79.2%**

## 1. Lead-time accuracy (hours before 4 PM ET anchor)

- **0h lead**: 81.1% within 2°F (MAE 1.15°F, n=365)
- **3h lead**: 80.9% within 2°F (MAE 1.17°F, n=366)
- **1h lead**: 80.8% within 2°F (MAE 1.16°F, n=364)
- **26h lead**: 80.8% within 2°F (MAE 1.20°F, n=364)
- **2h lead**: 80.5% within 2°F (MAE 1.17°F, n=365)

Median best lead hour per day: **36.0h** before anchor.

## 2. Weather-condition accuracy

- Best **forecast_stability** = **STABLE**: 85.7% within 2°F (n=6619)
- Best **observed_wdir_cardinal** = **SW**: 84.0% within 2°F (n=725)
- Best **forecast_wdir_cardinal** = **SE**: 85.4% within 2°F (n=2305)
- Best **range_bucket** = **narrow_<=1.5F**: 84.3% within 2°F (n=8355)

## 3. Seasonal accuracy

- Month **7**: 91.5% within 2°F (MAE 1.00°F)
- Month **11**: 91.0% within 2°F (MAE 0.79°F)
- Month **12**: 82.7% within 2°F (MAE 1.09°F)
- Month **8**: 82.3% within 2°F (MAE 1.31°F)
- Worst month **1**: 65.5% within 2°F

**Why seasons differ (Miami):** Winter dry-season days with steady easterly flow tend toward STABLE forecasts; summer convective afternoons and sea-breeze timing shift observed max earlier/later and widen forecast spread (UNSTABLE), lowering hit rate.
