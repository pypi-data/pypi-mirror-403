FROM --platform=linux/amd64 python:3.12.3-slim-bullseye
LABEL authors="fredrik"

COPY . /comp-manager
WORKDIR 'comp-manager'
ENTRYPOINT ["top", "-b"]
