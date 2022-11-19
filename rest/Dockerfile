FROM python:3.6-alpine
LABEL MAINTAINER="tgwalker93@gmail.com"

RUN pip3 install flask flask-wtf redis Flask-Debug jsonpickle minio
# install dependencies
RUN apk add -u zlib-dev jpeg-dev gcc musl-dev
RUN python3 -m pip install --upgrade pip
RUN pip3 install pillow

COPY ./minio-config.yaml /

WORKDIR /rest
COPY    rest-server.py /rest
CMD [ "python3", "rest-server.py"]
