# Legion5: enable virtualization for Docker + WSL

`systeminfo` reports:

```
Virtualization Enabled In Firmware: No
```

Docker and the `kmia-arch-ingest` Linux container **require this** to be **Yes**.

## Steps (one-time, ~2 minutes)

1. Reboot Legion5
2. Enter BIOS (Lenovo Legion: usually **F2** or **DEL** at startup)
3. Find **Intel Virtualization Technology** (may be under Advanced → CPU Configuration)
4. Set to **Enabled**
5. Save and exit (F10)

## After BIOS change

From your Mac:

```bash
ssh Legion5 "powershell -ExecutionPolicy Bypass -File E:\\KMIA_Setup\\11_post_reboot_container.ps1"
```

That will:
- Finish Ubuntu WSL install
- Start Docker Desktop
- Build `kmia-arch-ingest:latest` (same as NAS)
- Run 2020 year pipeline inside the container (reuses `E:\KMIA_Ingest` data)

## Already done

- Docker Desktop installed
- WSL 2.7.8 MSI installed
- Docker build context at `E:\KMIA_Ingest\docker\kmia-arch-ingest`
- Ingest scripts at `E:\KMIA_Ingest\scripts`
- April 2020 GRIBs already downloaded

## Interim

Native Git Bash + Windows `wgrib2` ingest was restarted until BIOS is fixed.
