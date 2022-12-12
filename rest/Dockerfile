FROM python:3.6-alpine
#FROM python:3.12-rc-bullseye

LABEL MAINTAINER="tgwalker93@gmail.com"

RUN pip3 install flask flask-wtf redis Flask-Debug jsonpickle minio
# install dependencies
RUN python3 -m pip install --upgrade pip
RUN apk add -u zlib-dev jpeg-dev gcc musl-dev
RUN pip3 install pillow
RUN pip3 install redis
RUN pip3 install flask
RUN pip3 install jsonpickle
RUN pip3 install minio

COPY ./minio-config.yaml /

WORKDIR /rest
COPY    rest-server.py /rest
# COPY . /rest
CMD [ "python3", "rest-server.py"]
