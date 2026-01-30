FROM python:3.13-slim

ARG CONFIG_PATH=config/config.example.yaml

ENV PATH="/root/.local/bin:${PATH}"

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl bash ca-certificates make \
    && rm -rf /var/lib/apt/lists/* \
    && curl -LsSf https://astral.sh/uv/install.sh | bash

WORKDIR /app
COPY . /app

RUN make install

ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:${PATH}"

COPY ${CONFIG_PATH} /app/config.yaml

RUN mkdir -p /app/logs
VOLUME ["/app/logs"]

CMD ["discord-llms", "--config", "/app/config.yaml"]
