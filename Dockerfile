FROM python:3.9-alpine

RUN apk add --no-cache \
    postgresql-dev python3-dev gcc g++ make zlib-dev jpeg-dev libpng-dev musl-dev libffi-dev openssl-dev \
    cairo-dev cairo cairo-tools pango pango-dev gdk-pixbuf \
    jpeg-dev zlib-dev freetype-dev lcms2-dev openjpeg-dev tiff-dev tk-dev tcl-dev \
    libxml2-dev libxslt-dev unzip wget fontconfig

RUN mkdir -p /usr/share/fonts
RUN wget "https://google-webfonts-helper.herokuapp.com/api/fonts/roboto?download=zip&subsets=latin&variants=regular" -O fonts.zip \
    && unzip fonts.zip \
    && cp roboto-v20-latin-regular.ttf /usr/share/fonts/Roboto.ttf \
    && rm roboto-v20-latin* fonts.zip \
    && fc-cache -fv

RUN apk del --no-cache \
        wget unzip

COPY requirements.txt /
RUN pip install -r /requirements.txt

COPY src/ /app

WORKDIR /app
