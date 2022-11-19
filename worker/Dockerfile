FROM python:3.8

FROM xserrat/facebook-demucs:latest
LABEL MAINTAINER="tgwalker93@gmail.com"

RUN pip install redis requests minio jsonpickle

RUN pip install minio
COPY ./minio-config.yaml /

WORKDIR /srv
COPY  worker.py /srv

RUN mkdir /srv/output

ENTRYPOINT [ "python3", "./worker.py"]


# USER root
# ENV TORCH_HOME=/data/models

# # Install Git
# RUN apt install git

# # Install Facebook Demucs
# RUN mkdir -p /lib/demucs

# WORKDIR /lib/demucs

# RUN git clone -b main --single-branch https://github.com/facebookresearch/demucs /lib/demucs

# RUN python3 -m pip install -e .
# RUN python3 -m demucs.separate -d cpu data/short-hop.mp3 # Trigger model download
# RUN rm -r separated  # cleanup

# VOLUME /data/input
# VOLUME /data/output
# VOLUME /data/models

# ENTRYPOINT ["/bin/bash", "--login", "-c"]