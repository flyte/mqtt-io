# If you get issues along the lines of:
# "Error while loading /usr/sbin/dpkg-split: No such file or directory"
# when building multiarch using buildx, then try this:
# https://github.com/docker/buildx/issues/495#issuecomment-761562905

FROM python:3.8-slim-buster AS base

ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8


FROM base AS requirements

# On linux/arm/v7 the cryptography package has no binary wheel, so we need its build
# dependencies. For rust, install the latest from rustup to avoid issues.
ARG TARGETPLATFORM
RUN if [ "${TARGETPLATFORM}" = "linux/arm/v7" ]; then \
        apt-get update && \
        apt-get install -y lsb-release curl g++ pkg-config libssl-dev libffi-dev && \
        \
        (curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | bash -s -- -y) \
    fi
ENV PATH="/root/.cargo/bin:${PATH}"


COPY pyproject.toml ./
RUN pip install --no-cache-dir poetry && \
    poetry export -o /requirements.txt && \
    mkdir -p /home/mqtt_io && \
    python -m venv /home/mqtt_io/venv && \
    /home/mqtt_io/venv/bin/pip install wheel


FROM base

# Install gcc so packages installed durring runtime may be build
RUN apt-get update && apt-get install -y gcc && gcc --version

RUN useradd -m -s /bin/bash mqtt_io
USER mqtt_io
WORKDIR /home/mqtt_io

COPY --from=requirements --chown=mqtt_io /home/mqtt_io/venv ./venv
COPY --from=requirements /requirements.txt ./
RUN venv/bin/python -m pip install --no-cache-dir --upgrade pip
RUN venv/bin/pip install --no-cache-dir -r requirements.txt

COPY --chown=mqtt_io mqtt_io mqtt_io
RUN gcc --version

CMD [ "venv/bin/python", "-m", "mqtt_io", "/config.yml" ]
