FROM golang:1.16-alpine as bomber
ENV REPO="github.com/codesenberg/bombardier"
ENV REPO_EDIT="github.com/PXEiYyMH8F/bombardier@78-add-proxy-support"
WORKDIR /app
RUN go mod init bombardier_tmp
RUN go mod edit -replace ${REPO}=${REPO_EDIT}
RUN go get ${REPO}
RUN CGO_ENABLED=0 go install -v -ldflags '-extldflags "-static"' ${REPO}
RUN /go/bin/bombardier --help

FROM python:3.10-alpine as builder
RUN apk update && apk add --update git gcc libc-dev libffi-dev
WORKDIR mhddos_proxy
COPY ./requirements.txt ./
RUN pip3 install --target=/mhddos_proxy/dependencies -r requirements.txt
COPY ./ ./

FROM python:3.10-alpine
WORKDIR mhddos_proxy
COPY --from=builder /mhddos_proxy .
COPY --from=bomber /go/bin/bombardier /root/go/bin/bombardier
ENV PYTHONPATH="${PYTHONPATH}:/mhddos_proxy/dependencies"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENTRYPOINT ["python3", "./runner.py"]
