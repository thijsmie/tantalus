FROM python:3.9-alpine

RUN apk add --no-cache \
    postgresql-dev python3-dev gcc make zlib-dev jpeg-dev libpng-dev musl-dev libffi-dev openssl-dev
RUN apk add --no-cache \
    libxml2-dev libxslt-dev

COPY requirements.txt /
RUN pip install -r /requirements.txt

COPY src/ /app

WORKDIR /app
