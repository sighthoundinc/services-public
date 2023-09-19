FROM python:3.8

# Install GStreamer and other dependencies
RUN apt-get update && apt-get install -y \
    libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev \
    libgstreamer-plugins-bad1.0-dev \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav \
    gstreamer1.0-tools \
    libgstrtspserver-1.0-dev \
    ffmpeg \
    libx264-dev \
    libpq-dev \
    python3-gi \
    curl \
    libcairo2-dev \
    libgirepository1.0-dev \
    gobject-introspection \
    pkg-config

# Install Python dependencies
WORKDIR /usr/src/app
COPY requirements.txt /usr/src/app/
RUN pip3 install -r requirements.txt

# Explicitly install PyGObject
RUN pip3 install PyGObject

# Environment Variables
ENV PYTHONPATH=${PYTHONPATH}:/usr/src/app/:/usr/src/app/lib/
ENV PYTHONUNBUFFERED=1
ENV GST_DEBUG=3

ENTRYPOINT [ "python3", "/usr/src/app/main.py" ]
