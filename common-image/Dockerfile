FROM agpipeline/base-image:1.0
LABEL maintainer="Chris Schnaufer <schnaufer@email.arizona.edu>"

# Build environment values
ARG arg_terrautil_url=https://github.com/terraref/terrautils.git
ENV terrautil_url=$arg_terrautil_url

ARG arg_terrautil_branch=master
ENV terrautil_branch=$arg_terrautil_branch

ARG arg_sensor_url=https://github.com/terraref/sensor-metadata.git
ENV sensor_url=$arg_sensor_url

ARG arg_sensor_branch=master
ENV sensor_branch=$arg_sensor_branch

# We need to explicitly set the user to root to install in system folders
USER root

# Install applications we need
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3-gdal \
        gdal-bin

# Install Python updates
RUN python3 -m pip install --upgrade --no-cache-dir pip 

RUN python3 -m pip install --upgrade --no-cache-dir setuptools
RUN python3 -m pip install --upgrade --no-cache-dir \
        numpy \
        influxdb \
        laspy \
        requests==2.21.0 \
        python-dateutil \
        utm \
        matplotlib \
        Pillow \
        scipy \
        cryptography \
        pyclowder

RUN apt-get install -y --no-install-recommends \
        libgdal-dev \
        gcc \
        g++ \
        python3-dev && \
    python3 -m pip install --upgrade --no-cache-dir \
        pygdal==2.2.3.5 && \
    apt-get remove -y \
        libgdal-dev \
        gcc \
        g++ \
        python3-dev && \
    apt-get autoremove -y

# Install from source
RUN apt-get install -y --no-install-recommends \
        git && \
    git clone $terrautil_url --branch $terrautil_branch --single-branch "/home/extractor/terrautil" && \
    python3 -m pip install "/home/extractor/terrautil/" && \
    rm -rf /home/extractor/terrautil && \
    git clone $sensor_url --branch $sensor_branch --single-branch "/home/extractor/sensor-metadata" && \
    mv "/home/extractor/sensor-metadata/sensors" "/home/extractor/sensors" && \
    rm -rf /home/extractor/sensor-metadata && \
    apt-get remove -y \
        git && \
    apt-get autoremove -y

# Perform some cleanup
RUN apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf ~/.cache/pip

# Set to the user we want to be
USER extractor

COPY *.py /home/extractor/
