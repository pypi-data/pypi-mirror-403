UV ?= uv
UVX ?= uvx

DATA_DIR = data
DOC_SOURCES != find ./docs -name '*.md'
PY_SOURCES != find ./filerohr -name '*.py'

help::
	@echo "  init            - initialize development environment"
	@echo "  clean           - clean generated files"
	@echo "  README.md       - update README.md from docs and python sources"

include make.d/test.mk
include make.d/release.mk

.PHONY: init
init:
	$(UV) sync --all-groups
	$(UVX) pre-commit autoupdate
	$(UVX) pre-commit install

clean::
	rm -rf \
		.venv

README.md: $(DOC_SOURCES) $(PY_SOURCES) Makefile
	cat docs/preface.md > "$@"
	printf "\n" >> "$@"
	cat docs/cli.md >> "$@"
	printf "\n" >> "$@"
	cat docs/configuration.md >> "$@"
	printf "\n" >> "$@"
	cat docs/tasks.md >> "$@"
	printf "\n" >> "$@"
	$(UV) run python -m filerohr list-jobs --base-heading-level 2 >> "$@"
	printf "\n" >> "$@"
	cat docs/custom-tasks.md >> "$@"
	npx prettier -w docs/ README.md
