FROM python:3.8

RUN apt update && apt install -y curl
RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && /usr/bin/python3 get-pip.py

WORKDIR /usr/src/app
COPY requirements.txt /usr/src/app/
RUN /usr/bin/python3 -m pip install -r requirements.txt

ENV PYTHONPATH=/usr/src/app/:/usr/src/app/lib/
ENV PYTHONUNBUFFERED=1

ENTRYPOINT [ "/usr/bin/python3", "/usr/src/app/aqueductRunner.py"]
