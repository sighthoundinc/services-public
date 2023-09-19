FROM python:3.8

RUN apt update && apt install -y curl

WORKDIR /usr/src/app
COPY requirements.txt /usr/src/app/
RUN pip3 install -r requirements.txt

ENV PYTHONPATH=${PYTHONPATH}:/usr/src/app/:/usr/src/app/lib/
ENV PYTHONUNBUFFERED=1

ENTRYPOINT [ "python3", "/usr/src/app/main.py" ]
