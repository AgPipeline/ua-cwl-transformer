FROM common-image
LABEL maintainer="Jorge Barrios <jorgebarrios@email.arizona.edu>"

USER root

RUN python3 -m pip install --upgrade --no-cache-dir setuptools
RUN python3 -m pip install --upgrade --no-cache-dir \
    pylint\
    pytest


COPY test-files/*.py /home/extractor/test-files/

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        git && \
    git clone https://github.com/AgPipeline/Organization-info.git /home/extractor/Organization-info 

RUN pylint \ 
    --rcfile=/home/extractor/Organization-info/pylint.rc *.py \
    --rcfile=/home/extractor/Organization-info/pylint.rc **/*.py

COPY test-files/*.sh /home/extractor/
RUN chmod a+x /home/extractor/test_entry.sh

USER extractor
ENTRYPOINT ["/home/extractor/test_entry.sh"]

RUN apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf ~/.cache/pip