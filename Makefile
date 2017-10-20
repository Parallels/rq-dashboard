TAG?=latest
IMAGENAME?=jtilander/rq-dashboard

.PHONY: image push all clean release force_release

all:
	@grep -Ee '^[a-z].*:' Makefile | cut -d: -f1 | grep -vF all

clean:
	rm -rf build/ dist/

release: clean
	# Check if latest tag is the current head we're releasing
	echo "Latest tag = $$(git tag | sort -nr | head -n1)"
	echo "HEAD SHA       = $$(git sha head)"
	echo "Latest tag SHA = $$(git tag | sort -nr | head -n1 | xargs git sha)"
	@test "$$(git sha head)" = "$$(git tag | sort -nr | head -n1 | xargs git sha)"
	make force_release

force_release: clean
	git push --tags
	python setup.py sdist bdist_wheel
	twine upload dist/*

image:
	docker build -t $(IMAGENAME):$(TAG) .

push: image
	docker push $(IMAGENAME):$(TAG) .

# Environment

env_create:
	virtualenv --python=python2.7 --no-site-packages .env

env:
	@echo source .env/bin/activate

env_install:
	pip install -r requirements.txt
