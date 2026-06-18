FROM archlinux:latest

ENV TZ=America/New_York
ENV PYTHONUNBUFFERED=1

RUN sed -i 's/^DownloadUser/#DownloadUser/' /etc/pacman.conf && \
    pacman -Syu --noconfirm && \
    pacman -S --noconfirm \
      base-devel git curl wget rsync ca-certificates tzdata \
      python python-pip python-virtualenv \
      aws-cli jq unzip gzip bzip2 xz zstd && \
    pacman -Scc --noconfirm

COPY install_toolchain.sh /usr/local/bin/install_toolchain.sh
RUN chmod +x /usr/local/bin/install_toolchain.sh && \
    /usr/local/bin/install_toolchain.sh

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

WORKDIR /data/KMIA_Ingest

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["sleep", "infinity"]
