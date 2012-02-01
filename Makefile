DEV_URL := "http://localhost:9181/"

all: help

help:
	@echo "Commands:"
	@echo "  run    Start the dev server at $(DEV_URL)"
	@echo "  open   Open a browser to $(DEV_URL)"
	@echo "  go     run && open at the same time"
	@echo

################
# Runtime stuff

run:
	python runserver.py

open:
	open $(DEV_URL)

go:
	(sleep 1; $(MAKE) open) &
	$(MAKE) run

clean:
	find . -name '*.pyc' -print0 | xargs -0 rm -r
