FROM archlinux:latest

ENV TZ=America/New_York
ENV PYTHONUNBUFFERED=1

RUN sed -i 's/^DownloadUser/#DownloadUser/' /etc/pacman.conf && \
    pacman -Syu --noconfirm && \
    pacman -S --noconfirm \
      base-devel bash curl wget rsync ca-certificates tzdata \
      python python-pip \
      jq \
    && pacman -Scc --noconfirm

COPY install_toolchain.sh /usr/local/bin/install_toolchain.sh
RUN chmod +x /usr/local/bin/install_toolchain.sh && \
    /usr/local/bin/install_toolchain.sh

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
COPY run_nas_policy_pipeline.sh /usr/local/bin/run_nas_policy_pipeline.sh
COPY run_nas_paper_loop.sh /usr/local/bin/run_nas_paper_loop.sh
COPY run_nas_orderbook_ws.sh /usr/local/bin/run_nas_orderbook_ws.sh
COPY load_kalshi_api_env_nas.sh /usr/local/bin/load_kalshi_api_env_nas.sh
COPY smoke_container.sh /usr/local/bin/smoke_container.sh

RUN chmod +x /usr/local/bin/entrypoint.sh \
    /usr/local/bin/run_nas_policy_pipeline.sh \
    /usr/local/bin/run_nas_paper_loop.sh \
    /usr/local/bin/run_nas_orderbook_ws.sh \
    /usr/local/bin/load_kalshi_api_env_nas.sh \
    /usr/local/bin/smoke_container.sh

WORKDIR /data

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["sleep", "infinity"]
