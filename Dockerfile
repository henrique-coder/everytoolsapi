FROM python:3.12.3-alpine

RUN apk add --no-cache --update \
    build-base \
    bash \
    git \
    wget \
    yasm \
    nasm \
    tar \
    x264-dev \
    x265-dev \
    libvpx-dev \
    fdk-aac-dev \
    lame-dev \
    opus-dev \
    && pip install --no-cache-dir -r /requirements.txt

RUN apk add --no-cache ffmpeg

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["gunicorn", "-b", "0.0.0.0:13579", "everytoolsapi:app"]
