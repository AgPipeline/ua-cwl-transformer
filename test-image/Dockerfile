FROM common-image
LABEL maintainer="Jorge Barrios <jorgebarrios@email.arizona.edu>"

USER root

RUN python3 -m pip install --upgrade --no-cache-dir setuptools
RUN python3 -m pip install --upgrade --no-cache-dir \
    pylint\
    pytest\
    matplotlib


COPY test-files/*.py /home/extractor/test-files/

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        git && \
    git clone https://github.com/AgPipeline/Organization-info.git /home/extractor/Organization-info 

#RUN pylint \ 
#   --rcfile=/home/extractor/Organization-info/pylint.rc /home/extractor/*.py \
#    --rcfile=/home/extractor/Organization-info/pylint.rc /home/extractor/test-files/*.py

COPY test-files/*.sh /home/extractor/
RUN chmod a+x /home/extractor/test_entry.sh

ENTRYPOINT ["/home/extractor/test_entry.sh"]