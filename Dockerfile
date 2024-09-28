FROM python:3.12-alpine

WORKDIR /app

COPY . .

ENTRYPOINT ["tail", "-f", "/dev/null"]
