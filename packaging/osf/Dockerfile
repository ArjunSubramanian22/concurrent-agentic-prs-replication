# Anonymous reproduction image. Default command is offline `make check`.
FROM python:3.12.8-bookworm

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    GIT_CONFIG_NOSYSTEM=1 \
    HOME=/home/repro \
    PYTHONPATH=/work/measurement:/work/semantic_conflicts/src:/work

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        git \
        make \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN git config --global user.email "repro@anonymous.example" \
    && git config --global user.name "anonymous"

WORKDIR /work
COPY requirements.txt pyproject.toml /tmp/build/
RUN pip install --no-cache-dir -r /tmp/build/requirements.txt

COPY . /work
RUN pip install --no-cache-dir -e ".[dev]"

CMD ["make", "check"]
