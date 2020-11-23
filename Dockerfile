FROM python:3.8-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        git \
		gcc \
		libc-dev \
	&& rm -rf /var/lib/apt/lists/*

RUN pip3 install setuptools==45 git+https://github.com/qcrisw/rq.git@ddb7a6c311e347e40cb27d312afb0e2cacdd28c2#egg=rq

ADD . /
RUN pip3 install -r requirements.txt
RUN python3 setup.py develop

EXPOSE 9181

ENTRYPOINT ["python3", "-m", "rq_dashboard"]
