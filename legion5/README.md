# Legion5 KMIA Ingest Processor

Legion5 (i5-10400, 16 GB, E: drive) runs the KMIA year ingest locally, then results can sync to NAS.

## Layout

```
E:\KMIA_Setup\          # bootstrap scripts (this folder)
E:\KMIA_Ingest\         # data root (same structure as NAS /data/KMIA_Ingest)
E:\Miniforge3\          # native Windows toolchain (fallback)
E:\WSL\                 # WSL distro (after reboot)
```

## Access (Mac)

### RDP (LAN)

| Field | Value |
|-------|-------|
| PC | `192.168.0.143` |
| Port | **3389** (default) |
| User | `CostcoLegion1` |

Use Microsoft Remote Desktop on home LAN. **IP changed from `192.168.0.127` → `192.168.0.143`** after the router/DHCP change ~11am.

### SSH

| Alias | Path | When to use |
|-------|------|-------------|
| `Legion5` | Tailscale MagicDNS | Remote (tailnet) |
| `Legion5Local` | `192.168.0.143:22` | Home LAN |
| `~/bin/ssh-legion5` | Auto-tries paths | When unsure |

```bash
ssh Legion5Local        # LAN SSH
ssh Legion5               # Tailscale SSH (when logged in)
```

## One-time setup (from Mac)

```bash
# Deploy + optimize + install WSL (may reboot Legion5)
ssh Legion5 "powershell -ExecutionPolicy Bypass -File E:\\KMIA_Setup\\run_setup.ps1"

# After reboot or if SSH dropped:
ssh Legion5 "powershell -ExecutionPolicy Bypass -File E:\\KMIA_Setup\\06_resume.ps1"

# If SSH/Tailscale lost (run on Legion5 locally or via RDP):
E:\KMIA_Setup\fix_ssh_and_optimize.cmd
```

## Monitor ingest

```bash
# WSL path:
ssh Legion5 "wsl -d Ubuntu -- tail -f /mnt/e/KMIA_Ingest/logs/ingestion/legion5_year_2020_pipeline.log"

# Native Git Bash path:
ssh Legion5 "\"C:\\Program Files\\Git\\bin\\bash.exe\" -lc 'tail -f /e/KMIA_Ingest/logs/ingestion/legion5_year_2020_pipeline.log'"
```

## Auto-resume on boot

Copy `resume.cmd` to Startup folder on Legion5 (done by 06_resume if admin):

```
shell:startup  →  E:\KMIA_Setup\resume.cmd
```

## Year ingested

2020 Apr–Dec (earliest AWS NDFD date: 2020-04-16).
