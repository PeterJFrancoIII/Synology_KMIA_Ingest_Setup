# Legion5 <-> MediaServer2 Connection

## Problem (what we hit)
- **SCP fails** on Synology — no `scp` subsystem (SFTP only)
- **gzip tar over LAN** wastes CPU; GRIB files are already compressed
- **No SSH config** on Legion5 — repeated handshakes every month pull
- **Wrong month paths** — NAS may use `8` or `08` folder names

## Solution
| Optimization | Effect |
|--------------|--------|
| **LAN direct** `192.168.0.193:23921` | <1ms ping (same subnet as Legion5 Ethernet) |
| **Uncompressed tar** `tar cf` / `tar xf` | ~2-3x faster than `tar czf` on GRIB |
| **SSH ControlMaster** | One connection reused for all pulls |
| **`nas-local` host alias** | Clean config, no hardcoded keys in scripts |
| **Month path resolver** | Tries `08` and `8` automatically |

## One-time setup on Legion5

From Mac (deploy setup repo to `E:\KMIA_Setup` first), or copy files manually:

```powershell
# On Legion5 — after files are in E:\KMIA_Setup
powershell -ExecutionPolicy Bypass -File E:\KMIA_Setup\legion5\40_optimize_nas_connection.ps1
```

Or from Mac:

```bash
scp -r "Synology_KMIA_Ingest_Setup/legion5/config" "Synology_KMIA_Ingest_Setup/legion5/nas_pull_helpers.sh" \
  "Synology_KMIA_Ingest_Setup/legion5/40_optimize_nas_connection.ps1" \
  "Synology_KMIA_Ingest_Setup/legion5/41_benchmark_nas_connection.sh" \
  Legion5:E:/KMIA_Setup/legion5/
```

## Benchmark

```bash
bash /d/KMIA_Process/scripts/41_benchmark_nas_connection.sh
```

Compares compressed vs uncompressed tar for one day of GRIB.

## Environment (Git Bash)

```bash
export NAS_SSH_HOST=nas-local      # use nas-remote when away from LAN
export NAS_TAR_COMPRESS=no         # yes only over internet
export NAS_ROOT=/volume2/Data/App_Development/KMIA_Ingest
```

## Network notes
- Legion5 **Ethernet** `192.168.0.143` → NAS `192.168.0.193` (optimal)
- Default route is Ethernet (Surfshark VPN does not hijack LAN)
- Tailscale (`100.93.x`) available but **slower** — use only off-LAN

## SMB (recommended on LAN)

SMB with multithreaded `robocopy` is faster than single-stream `ssh | tar` for ~40 GB/month pulls.

**One-time setup on Legion5:**

```powershell
powershell -ExecutionPolicy Bypass -File D:\KMIA_Process\scripts\43_setup_nas_smb.ps1
```

**Git Bash env** (auto-detects `Z:` when `NAS_SMB_DRIVE` is set):

```bash
export NAS_SMB_DRIVE=Z:
export KMIA_EXTRACT_WORKERS=4
export NAS_PULL_MODE=smb   # optional; auto-selected when Z: is mounted
```

**Benchmark tar vs SMB:**

```bash
bash /d/KMIA_Process/scripts/43_benchmark_pull_modes.sh
```

Share path: `\\192.168.0.193\Data\App_Development\KMIA_Ingest\raw\...`

SMB uses dedicated read-only NAS user `kmia_legion5` (password in `D:\KMIA_Process\secrets\nas_smb_password` on Legion5 only — not in repo).

## Parallel wgrib2 extract

`22_batch_extract_local_gribs.py --workers 4` (default via `KMIA_EXTRACT_WORKERS`) runs
multiple `wgrib2` processes — set in `35_process_month_from_nas.sh`.
