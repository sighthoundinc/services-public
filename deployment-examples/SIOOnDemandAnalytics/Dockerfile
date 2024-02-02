FROM ubuntu:20.04

ARG PYTHONVER=3

RUN apt-get update &&\
    apt-get install -y python${PYTHONVER} &&\
    apt-get install -y python${PYTHONVER}-dev &&\
    apt-get install -y python${PYTHONVER}-distutils &&\
    apt-get install -y python${PYTHONVER}-pip &&\
    python${PYTHONVER} -m pip install --upgrade pip

WORKDIR /rest

COPY ./requirements.txt /rest


RUN pip${PYTHONVER} --no-cache-dir install -r requirements.txt

COPY ./restApi.py /rest/

EXPOSE 8080

CMD ["python3", "restApi.py"]

