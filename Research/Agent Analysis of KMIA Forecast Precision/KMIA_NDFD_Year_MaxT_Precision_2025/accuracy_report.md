# KMIA_NDFD_Year_MaxT_Precision_2025

- Target dates analyzed: **238**
- Forecast releases (0–36h before 4 PM ET): **8772**
- Overall MAE: **1.21°F**
- Overall within 2°F: **77.2%**

## 1. Lead-time accuracy (hours before 4 PM ET anchor)

- **0h lead**: 82.3% within 2°F (MAE 1.07°F, n=237)
- **1h lead**: 81.4% within 2°F (MAE 1.10°F, n=236)
- **2h lead**: 80.4% within 2°F (MAE 1.10°F, n=235)
- **3h lead**: 78.6% within 2°F (MAE 1.14°F, n=238)
- **20h lead**: 78.6% within 2°F (MAE 1.22°F, n=238)

Median best lead hour per day: **35.0h** before anchor.

## 2. Weather-condition accuracy

- Best **forecast_stability** = **STABLE**: 81.5% within 2°F (n=4634)
- Best **observed_wdir_cardinal** = **W**: 85.8% within 2°F (n=295)
- Best **forecast_wdir_cardinal** = **SE**: 85.5% within 2°F (n=3083)
- Best **range_bucket** = **narrow_<=1.5F**: 80.9% within 2°F (n=5818)

## 3. Seasonal accuracy

- Month **4**: 90.3% within 2°F (MAE 0.87°F)
- Month **3**: 83.5% within 2°F (MAE 1.04°F)
- Month **5**: 83.3% within 2°F (MAE 0.85°F)
- Month **6**: 81.4% within 2°F (MAE 1.17°F)
- Worst month **1**: 61.1% within 2°F

**Why seasons differ (Miami):** Winter dry-season days with steady easterly flow tend toward STABLE forecasts; summer convective afternoons and sea-breeze timing shift observed max earlier/later and widen forecast spread (UNSTABLE), lowering hit rate.
