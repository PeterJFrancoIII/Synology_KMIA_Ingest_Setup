# KMIA_NDFD_Year_MaxT_Precision_2022

- Target dates analyzed: **365**
- Forecast releases (0–36h before 4 PM ET): **13455**
- Overall MAE: **1.35°F**
- Overall within 2°F: **72.5%**

## 1. Lead-time accuracy (hours before 4 PM ET anchor)

- **0h lead**: 76.9% within 2°F (MAE 1.20°F, n=364)
- **1h lead**: 76.9% within 2°F (MAE 1.21°F, n=364)
- **2h lead**: 76.4% within 2°F (MAE 1.22°F, n=365)
- **7h lead**: 76.1% within 2°F (MAE 1.24°F, n=364)
- **3h lead**: 75.3% within 2°F (MAE 1.25°F, n=365)

Median best lead hour per day: **36.0h** before anchor.

## 2. Weather-condition accuracy

- Best **forecast_stability** = **STABLE**: 78.4% within 2°F (n=7207)
- Best **observed_wdir_cardinal** = **SE**: 80.0% within 2°F (n=3527)
- Best **forecast_wdir_cardinal** = **SE**: 80.9% within 2°F (n=2283)
- Best **range_bucket** = **narrow_<=1.5F**: 77.6% within 2°F (n=9391)

## 3. Seasonal accuracy

- Month **3**: 89.7% within 2°F (MAE 0.84°F)
- Month **7**: 84.1% within 2°F (MAE 0.91°F)
- Month **5**: 80.2% within 2°F (MAE 1.17°F)
- Month **6**: 79.9% within 2°F (MAE 1.20°F)
- Worst month **11**: 51.8% within 2°F

**Why seasons differ (Miami):** Winter dry-season days with steady easterly flow tend toward STABLE forecasts; summer convective afternoons and sea-breeze timing shift observed max earlier/later and widen forecast spread (UNSTABLE), lowering hit rate.
