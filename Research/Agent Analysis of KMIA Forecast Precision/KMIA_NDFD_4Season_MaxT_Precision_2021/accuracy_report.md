# KMIA_NDFD_4Season_MaxT_Precision_2021

- Target dates analyzed: **126**
- Forecast releases (0–36h before 4 PM ET): **4530**
- Overall MAE: **1.20°F**
- Overall within 2°F: **77.3%**

## 1. Lead-time accuracy (hours before 4 PM ET anchor)

- **25h lead**: 82.6% within 2°F (MAE 1.10°F, n=121)
- **26h lead**: 82.0% within 2°F (MAE 1.12°F, n=122)
- **27h lead**: 82.0% within 2°F (MAE 1.12°F, n=122)
- **22h lead**: 81.8% within 2°F (MAE 1.12°F, n=121)
- **21h lead**: 81.3% within 2°F (MAE 1.11°F, n=123)

Median best lead hour per day: **36.0h** before anchor.

## 2. Weather-condition accuracy

- Best **forecast_stability** = **STABLE**: 83.3% within 2°F (n=2142)
- Best **observed_wdir_cardinal** = **SE**: 89.3% within 2°F (n=1148)
- Best **forecast_wdir_cardinal** = **NW**: 97.3% within 2°F (n=74)
- Best **range_bucket** = **narrow_<=1.5F**: 81.1% within 2°F (n=3161)

## 3. Seasonal accuracy

### Four-season sample (one month per season)

- **Fall** (month 11): 100.0% within 2°F, 100.0% within 1°F, MAE 0.99°F (n=17 forecasts, 1 days)
- **Summer** (month 8): 100.0% within 2°F, 100.0% within 1°F, MAE 0.20°F (n=17 forecasts, 1 days)
- **Fall** (month 10): 85.6% within 2°F, 76.7% within 1°F, MAE 0.99°F (n=1128 forecasts, 31 days)
- **Summer** (month 7): 82.3% within 2°F, 70.4% within 1°F, MAE 1.10°F (n=1131 forecasts, 31 days)
- **Winter** (month 12): 81.5% within 2°F, 72.2% within 1°F, MAE 1.12°F (n=1126 forecasts, 31 days)
- **Spring** (month 4): 59.5% within 2°F, 52.7% within 1°F, MAE 1.59°F (n=1094 forecasts, 30 days)
- **Spring** (month 5): 17.6% within 2°F, 17.6% within 1°F, MAE 1.88°F (n=17 forecasts, 1 days)

### Best lead hour by season (highest % within 2°F)

- **Winter**: 10h lead — 87.1% within 2°F
- **Spring**: 27h lead — 66.7% within 2°F
- **Summer**: 30h lead — 90.3% within 2°F
- **Fall**: 24h lead — 93.5% within 2°F
- Month **8**: 100.0% within 2°F (MAE 0.20°F)
- Month **11**: 100.0% within 2°F (MAE 0.99°F)
- Month **10**: 85.6% within 2°F (MAE 0.99°F)
- Month **7**: 82.3% within 2°F (MAE 1.10°F)
- Worst month **5**: 17.6% within 2°F

**Why seasons differ (Miami):** Winter dry-season days with steady easterly flow tend toward STABLE forecasts; summer convective afternoons and sea-breeze timing shift observed max earlier/later and widen forecast spread (UNSTABLE), lowering hit rate.
