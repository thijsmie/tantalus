FROM python:3.9-alpine

RUN apk add --no-cache \
    postgresql-dev python3-dev py3-gevent

COPY requirements.txt /
RUN pip install -r /requirements.txt

COPY src/ /app
COPY config/production.json /app/conf.json

WORKDIR /app
