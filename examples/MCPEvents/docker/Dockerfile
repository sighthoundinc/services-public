FROM python:3.9

RUN apt-get update && apt-get install -y ffmpeg libx264.dev

RUN mkdir -p /usr/src/app

WORKDIR /usr/src/app

COPY MCPEvents/requirements.txt /usr/src/app/
RUN pip3 install -r requirements.txt

RUN mkdir -p /usr/src/lib
COPY lib /usr/src/lib
COPY MCPEvents/. /usr/src/app/
