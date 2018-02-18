FROM ubuntu:18.04
MAINTAINER Andrew Dunai

ARG HOST_USER
ARG HOST_UID

ENV PYTHONIOENCODING UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

RUN apt-get update
RUN apt-get install -y python3.6-dev python3-pip libvlc-dev vlc locales language-pack-en wget

RUN locale-gen en_US.UTF-8

RUN useradd ${HOST_USER} -m -G audio -u ${HOST_UID}

WORKDIR /home/${HOST_USER}

RUN wget https://launchpad.net/ubuntu/+archive/primary/+files/python3-stdlib-extensions_3.6.4.orig.tar.xz && \
    tar -xvf python3-stdlib-extensions_3.6.4.orig.tar.xz && \
    cp -r python3-stdlib-extensions-3.6.4/3.6/Lib/lib2to3/ /usr/lib/python3.6/ && \
    rm -rf python3-stdlib-extensions-3.6.4 python3-stdlib-extensions-3.6.4.orig.tar.xz

COPY requirements.txt .

RUN python3.6 -m pip install -r requirements.txt

RUN echo "default-server = 172.17.0.1" >> /etc/pulse/client.conf
ENV PULSE_SERVER 172.17.0.1

USER ${HOST_USER}
RUN mkdir .config

COPY clay ./clay
