# Data Source Map — KMIA Forecast And Observation Ingest

**Station:** KMIA (Miami International Airport)  
**Lat/Lon:** 25.7906, -80.3164 (NWS MapClick / MFL/105,51)

Canonical config: `ingest/config/kmia_station.json` (mirrored in Kalshi `backend/src/shared/kmia_station.py`).  
**ISD:** USAF 722020, WBAN 12839

## Forecast Sources

| Source | Role | History |
|---|---|---|
| AWS Open Data NDFD (`noaa-ndfd-pds`) | Primary historical NDFD archive | 2020-04-16 onward |
| NCEI THREDDS NDFD | Catalog browsing, spot retrieval, gap checks | Variable |
| NCEI AIRS NDFD by WMO header | Long-history pre-2020 backfill | 2004-06-06 onward |

### NDFD Rules

1. NDFD is **forecast** data, not observed data.
2. Do **not** infer release time from filenames. Use GRIB ref time (`d=`) for release and valid time (`vt=`) for the forecast element. Do not assume fixed 00/06/12/18 UTC cycles.
3. Use `wgrib2` or `grib2io` first for NDFD GRIB2 work.
4. Do **not** hard-code a grid cell for KMIA. Derive nearest point from each GRIB file.
5. Start with nearest-grid extraction for reproducibility.

**Point extract detail:** [GRIB_CSV_Extraction.md](GRIB_CSV_Extraction.md)

### NDFD Variables (normalized)

```text
maxt
temp
td
sky
wdir
wspd
pop12
qpf
```

## Observation / Verification Sources

| Source | Role |
|---|---|
| NCEI ISD / ISD-Lite / LCD | KMIA station observation truth and station history |
| NOMADS RTMA | Near-real-time gridded analysis companion |
| NOMADS URMA | Final gridded analysis companion |
| Synoptic / MADIS / HF-ASOS | Fast operational layer, not final settlement truth |

## Storage Layout

```text
/volume2/Data/App_Development/KMIA_Ingest/
  raw/forecast/ndfd_aws/{maxt,temp,td,sky,wdir,wspd,pop12,qpf}/YYYY/MM/DD/
  raw/forecast/{ndfd_thredds,ndfd_airs}/
  raw/observed/{isd,isd_lite,lcd,rtma,urma,synoptic,madis}/
  processed/{messages,points,daily,joins,parquet,csv}/
  manifest/{files.parquet,messages.parquet,retries.parquet,gaps.parquet,run_log.jsonl}
```

## Manifest Fields

Each ingested file should append a record with:

- `source`, `source_path`, `retrieved_at_utc`
- `sha256`, `content_length`
- `format`, `station_id`, `station_lat`, `station_lon`
- `decoder`, `status`, `error_text`
