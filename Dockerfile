# Reproduction image for the Concurrent Agentic PRs study.
# merge-tree output depends on the git version and on merge/rename settings.
# This image pins both. Replay always also passes the -c flags in analysis/lib/gitenv.py.
FROM python:3.12.8-bookworm

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    GIT_CONFIG_NOSYSTEM=1 \
    HOME=/home/repro

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        git \
        make \
        texlive-latex-base \
        texlive-latex-recommended \
        texlive-latex-extra \
        texlive-fonts-recommended \
        texlive-publishers \
        lmodern \
        latexmk \
        ca-certificates \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Record exact package versions into the image so a reviewer can see them
# without running the analysis. Replay still overrides gitconfig via -c.
RUN git --version > /opt/git-version.txt \
    && python --version > /opt/python-version.txt \
    && git config --global merge.conflictStyle merge \
    && git config --global diff.renameLimit 400 \
    && git config --global merge.renames true \
    && git config --global diff.renames true \
    && git config --global user.email "repro@anonymous.example" \
    && git config --global user.name "anonymous"

WORKDIR /work
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY . /work
RUN mkdir -p /home/repro \
    && python scripts/record_env.py --out /opt/environment_record.json || true

# Default: regenerate tables and figures from committed snapshot
# (no live GitHub). Live steps are `make replay` and `make collect`.
CMD ["make", "all"]
