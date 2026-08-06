FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ffmpeg \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /work

COPY docker/app/requirements.txt /tmp/requirements.txt
RUN python -m pip install \
        --no-cache-dir \
        --break-system-packages \
        -r /tmp/requirements.txt

COPY docker/app/generate_audio.py /opt/narrator/generate_audio.py
COPY docker/app/generate_dict.py /opt/narrator/generate_dict.py
COPY --chmod=755 docker/entrypoint /entrypoint

ENTRYPOINT ["/entrypoint"]
CMD ["--help"]
