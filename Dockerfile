FROM --platform=$TARGETPLATFORM python:3.10-slim as builder

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY ./requirements.txt .
RUN python3 -m pip install --no-cache-dir wheel
RUN python3 -m pip install --no-cache-dir --only-binary=:all: -r requirements.txt

FROM --platform=$TARGETPLATFORM python:3.10-slim
COPY --from=builder	/opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
WORKDIR mhddos_proxy
COPY . .
ENTRYPOINT ["python3", "./runner.py"]
