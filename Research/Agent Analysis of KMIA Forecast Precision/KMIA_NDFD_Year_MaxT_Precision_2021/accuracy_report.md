# KMIA_NDFD_Year_MaxT_Precision_2021

- Target dates analyzed: **365**
- Forecast releases (0–36h before 4 PM ET): **13452**
- Overall MAE: **1.17°F**
- Overall within 2°F: **79.2%**

## 1. Lead-time accuracy (hours before 4 PM ET anchor)

- **22h lead**: 81.2% within 2°F (MAE 1.15°F, n=362)
- **21h lead**: 81.0% within 2°F (MAE 1.14°F, n=364)
- **0h lead**: 80.9% within 2°F (MAE 1.10°F, n=362)
- **2h lead**: 80.8% within 2°F (MAE 1.12°F, n=365)
- **15h lead**: 80.8% within 2°F (MAE 1.15°F, n=365)

Median best lead hour per day: **36.0h** before anchor.

## 2. Weather-condition accuracy

- Best **forecast_stability** = **STABLE**: 84.2% within 2°F (n=6565)
- Best **observed_wdir_cardinal** = **SE**: 88.0% within 2°F (n=3715)
- Best **forecast_wdir_cardinal** = **SE**: 90.8% within 2°F (n=2834)
- Best **range_bucket** = **narrow_<=1.5F**: 82.8% within 2°F (n=8922)

## 3. Seasonal accuracy

- Month **8**: 91.8% within 2°F (MAE 0.76°F)
- Month **1**: 88.8% within 2°F (MAE 1.06°F)
- Month **10**: 84.4% within 2°F (MAE 1.03°F)
- Month **2**: 82.6% within 2°F (MAE 1.30°F)
- Worst month **4**: 58.6% within 2°F

**Why seasons differ (Miami):** Winter dry-season days with steady easterly flow tend toward STABLE forecasts; summer convective afternoons and sea-breeze timing shift observed max earlier/later and widen forecast spread (UNSTABLE), lowering hit rate.
