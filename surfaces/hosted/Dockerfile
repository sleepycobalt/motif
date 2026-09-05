# Motif hosted engine. Build context is the repository root:
#   fly deploy -c surfaces/hosted/fly.toml
FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY core core
COPY synth synth
COPY surfaces surfaces
RUN pip install --no-cache-dir ".[hosted]"

ENV MOTIF_RUNS_DIR=/data/runs \
    MOTIF_WORK_DIR=/tmp/motif \
    PORT=8080
RUN mkdir -p /tmp/motif

EXPOSE 8080
CMD ["motif-hosted"]
