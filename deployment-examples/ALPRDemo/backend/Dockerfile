FROM python:3.9

WORKDIR /usr/src/app
COPY requirements.txt /usr/src/app/
COPY entrypoint.sh /usr/src/app/
COPY rest.py /usr/src/app/
RUN pip3 install -r requirements.txt

ENV PYTHONPATH=${PYTHONPATH}:/usr/src/app:/usr/src/app/common:/usr/src/app/lib
ENV PYTHONUNBUFFERED=1



ENTRYPOINT [ "/bin/bash", "-c", "/usr/src/app/entrypoint.sh" ]
