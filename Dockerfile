FROM python:3.6-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
		dos2unix \
		gcc \
		libc-dev \
	&& rm -rf /var/lib/apt/lists/*

ENV TINI_VERSION v0.17.0
ADD https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini /tini
RUN chmod +x /tini

ENV RQ_VERSION 0.10.0
RUN pip3 install rq==$RQ_VERSION

ADD autoexec.sh /
RUN dos2unix /autoexec.sh
RUN chmod a+x /autoexec.sh

RUN mkdir /app
WORKDIR /app
ADD . /app
RUN pip3 install -r /app/requirements.txt
RUN python3 setup.py develop

ENV PORT 80
EXPOSE $PORT

ENV REDIS_URL redis://redis
ENV USERNAME rq
ENV PASSWORD password
ENV URL_PREFIX /

ENTRYPOINT ["/tini", "--", "/autoexec.sh"]
CMD ["web"]
