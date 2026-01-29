PYTHON ?= $(UV) run python

SOURCE_FILES != find ./filerohr ./tests -type f -not -name '*.pyc'
TEST_FILES ?= tests

.PHONY: ruff
ruff:
	$(UV) run ruff format $(FORMAT_ARGS)
	$(UV) run ruff check $(CHECK_ARGS)

.PHONY: lint
lint:
	$(MAKE) ruff FORMAT_ARGS=--check

.PHONY: format style
style format:
	$(MAKE) ruff CHECK_ARGS=--fix

.coverage: $(SOURCE_FILES)
	$(UV) run --env-file .env.test python -m coverage run --source=filerohr -m pytest $(TEST_FILES)

.PHONY: test
test:
	@$(MAKE) --always-make .coverage

.PHONY: coverage
coverage: .coverage
	$(PYTHON) -m coverage report
	$(PYTHON) -m coverage xml

help::
	@echo "  style           - apply formatting"
	@echo "  lint            - run linters"
	@echo "  test            - run test suite"
	@echo "  coverage        - generate coverage reports"

clean::
	rm -rf \
		.coverage \
		coverage.xml
