FROM python:3.9

WORKDIR /usr/src/app
COPY restServerStub.py /usr/src/app/
RUN pip3 install flask pillow

ENV PYTHONPATH=${PYTHONPATH}:/usr/src/app:/usr/src/app/common:/usr/src/app/lib
ENV PYTHONUNBUFFERED=1



ENTRYPOINT [ "python3", "/usr/src/app/restServerStub.py" ]
