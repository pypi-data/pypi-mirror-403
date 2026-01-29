.PHONY: docs
docs:
	(cd docs; make html)

.PHONY: test
test:
	hatch run test

.PHONY: lint
lint:
	hatch run lint:typing
	hatch run lint:style

.PHONY: lint-docs
lint-docs:
	hatch run lint:docs

.PHONY: fmt
fmt:
	hatch run lint:fmt

.PHONY: build
build:
	hatch build
