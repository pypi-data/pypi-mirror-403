# https://hub.docker.com/_/python
FROM python:3.13-slim-trixie

# for pip cache:
ENV XDG_CACHE_HOME=/tmp/.cache
ENV PIP_CACHE_DIR=/tmp/.cache
ENV UV_CACHE_DIR=/tmp/.cache

ENV PYTHONUNBUFFERED=1

# Install deps
RUN set -x \
    && apt-get update \
    && apt-get install -y postgresql-client python3-venv \
    && rm -rf /var/lib/apt \
    && python3 -m pip install -U pip

WORKDIR /django

COPY . ./

# Bootstrap: The first manage.py call will create the .venv
RUN ./manage.py version
