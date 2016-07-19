# Environment

env_create:
	virtualenv --python=python2.7 --no-site-packages .env

env:
	@echo source .env/bin/activate

env_install:
	pip install -r requirements.txt
