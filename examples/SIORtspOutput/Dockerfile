FROM python:3.8

RUN apt-get update && apt-get install -y \
    libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev \
    libgstreamer-plugins-bad1.0-dev \
    gstreamer1.0-plugins-base gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav \
    gstreamer1.0-tools \
    libgstrtspserver-1.0-dev

RUN apt-get update && apt-get install -y \
    ffmpeg \ 
    libx264.dev \
    libpq-dev \
    python3-gi \
    curl \
    libcairo2-dev \
    libgirepository1.0-dev

RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && /usr/bin/python3 get-pip.py

WORKDIR /usr/src/app
COPY requirements.txt /usr/src/app/
RUN /usr/bin/python3 -m pip install -r requirements.txt

ENV PYTHONPATH=/usr/src/app/:/usr/src/app/lib/
ENV PYTHONUNBUFFERED=1
ENV GST_DEBUG=3

ENTRYPOINT [ "/usr/bin/python3", "/usr/src/app/main.py" ]
