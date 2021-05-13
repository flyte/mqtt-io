# If you get issues along the lines of:
# "Error while loading /usr/sbin/dpkg-split: No such file or directory"
# when building multiarch using buildx, then try this:
# https://github.com/docker/buildx/issues/495#issuecomment-761562905

FROM python:3.8-buster AS base

ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8


FROM base AS requirements

ARG BUILDX_QEMU_ENV
RUN apt-get update && \
    apt-get install -y lsb-release rustc libssl-dev libffi-dev python3-venv && \
    apt-get clean && \
    rm -rf /var/lib/apt-/lists/*

# This nonsense is required for this reason:
# https://github.com/JonasAlfredsson/docker-nginx-certbot/issues/30

RUN pip install --no-cache-dir wheel setuptools-rust && \
    if [ "${BUILDX_QEMU_ENV}" = "true" -a "$(getconf LONG_BIT)" = "32" ]; then \
        pip install --no-cache-dir cryptography==3.3.2; \
    fi && \
    pip install --no-cache-dir poetry

COPY pyproject.toml ./
RUN poetry export -o /requirements.txt && \
    mkdir -p /home/mqtt_io && \
    python -m venv /home/mqtt_io/venv && \
    /home/mqtt_io/venv/bin/pip install wheel


FROM base

RUN useradd -m -s /bin/bash mqtt_io
USER mqtt_io
WORKDIR /home/mqtt_io

COPY --from=requirements --chown=mqtt_io /home/mqtt_io/venv ./venv
COPY --from=requirements /requirements.txt ./
RUN venv/bin/pip install -r requirements.txt

COPY --chown=mqtt_io mqtt_io mqtt_io

CMD [ "venv/bin/python", "-m", "mqtt_io", "/config.yml" ]
