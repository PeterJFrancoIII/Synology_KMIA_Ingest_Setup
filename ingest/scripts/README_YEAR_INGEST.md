# Full-year KMIA NAS ingest

AWS NDFD `wmo/` data on `noaa-ndfd-pds` begins **2020-04-16**. There is no Jan–Mar 2020 on S3.

| Year | Months ingested | Notes |
|------|-----------------|-------|
| **2020** | Apr–Dec (9 months) | Earliest available; partial calendar year |
| **2021+** | Jan–Dec (12 months) | First complete calendar year: **2021** |

## Run on NAS

```bash
# Deploy scripts from Mac setup_repo, then:
sudo docker exec -d kmia-arch-ingest bash -lc \
  'nohup bash /data/KMIA_Ingest/scripts/27_nas_year_pipeline.sh 2020 \
   > /data/KMIA_Ingest/logs/ingestion/nas_year_2020.nohup.log 2>&1 &'

# Monitor:
tail -f /data/KMIA_Ingest/logs/ingestion/nas_year_2020_pipeline.log
```

## Outputs

```
processed/points/station=KMIA/
  ndfd_kmia_point_forecasts_VALID_ONLY_2020.csv
  kmia_ncei_global_hourly_2020.csv
  kmia_2020_PLUS_mean_median_stability_wind_points.csv
  kmia_2020_PLUS_mean_median_stability_wind_daily_summary.csv
  kmia_2020_stability_wind.png
  monthly/2020/   # per-month VALID_ONLY (retained)
  yearly/         # merged maxt + wdir year files
```

## Est. size (2020 Apr–Dec)

- Raw GRIB (if kept): ~12–14 GB
- Merged VALID_ONLY CSV: ~350–400 MB
- Processed chart CSVs: ~2 MB

## After 2020

```bash
bash /data/KMIA_Ingest/scripts/27_nas_year_pipeline.sh 2021
```

Each year needs matching ISD: `ISD_YEAR=2021` via step 1 in pipeline.
