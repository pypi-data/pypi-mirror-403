FROM docker.io/python:3.9-slim

SHELL [ "/bin/bash", "-c"]

RUN apt update &&  apt-get install -y git
COPY . eossr
RUN cd eossr; pip install .; cd ..
RUN rm -rf eossr

ENTRYPOINT /bin/bash
