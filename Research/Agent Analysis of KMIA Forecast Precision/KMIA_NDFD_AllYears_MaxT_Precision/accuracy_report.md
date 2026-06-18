# KMIA_NDFD_AllYears_MaxT_Precision

- Target dates analyzed: **258**
- Forecast releases (0–36h before 4 PM ET): **9460**
- Overall MAE: **1.49°F**
- Overall within 2°F: **70.3%**

## 1. Lead-time accuracy (hours before 4 PM ET anchor)

- **21h lead**: 73.4% within 2°F (MAE 1.47°F, n=256)
- **20h lead**: 73.0% within 2°F (MAE 1.46°F, n=256)
- **19h lead**: 72.3% within 2°F (MAE 1.46°F, n=256)
- **18h lead**: 72.3% within 2°F (MAE 1.48°F, n=256)
- **17h lead**: 72.3% within 2°F (MAE 1.47°F, n=256)

Median best lead hour per day: **33.5h** before anchor.

## 2. Weather-condition accuracy

- Best **forecast_stability** = **STABLE**: 78.7% within 2°F (n=3934)
- Best **observed_wdir_cardinal** = **SE**: 80.9% within 2°F (n=2737)
- Best **forecast_wdir_cardinal** = **N**: 91.9% within 2°F (n=160)
- Best **range_bucket** = **narrow_<=1.5F**: 75.3% within 2°F (n=5155)

## 3. Seasonal accuracy

- Month **8**: 80.0% within 2°F (MAE 1.31°F)
- Month **11**: 79.2% within 2°F (MAE 1.02°F)
- Month **9**: 76.6% within 2°F (MAE 1.26°F)
- Month **12**: 75.1% within 2°F (MAE 1.65°F)
- Worst month **4**: 40.5% within 2°F

**Why seasons differ (Miami):** Winter dry-season days with steady easterly flow tend toward STABLE forecasts; summer convective afternoons and sea-breeze timing shift observed max earlier/later and widen forecast spread (UNSTABLE), lowering hit rate.
