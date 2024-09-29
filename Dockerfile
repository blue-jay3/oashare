FROM python:3.12-alpine

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY . .

ENTRYPOINT [ "/app/docker-entrypoint.sh" ]
