SRC_FILES:=src tests
UV:=$(shell which uv)

VENV:=.venv
VENV_BIN:=${VENV}/bin

PYTHON:=${VENV_BIN}/python
RUFF:=${VENV_BIN}/ruff
PYRIGHT:=${VENV_BIN}/pyright
PYTEST:=${VENV_BIN}/pytest

${VENV}: pyproject.toml
	${UV} python install
	${UV} venv ${VENV}
	${UV} sync --all-extras

.PHONY: ci
ci: lint test ## Run CI

.PHONY: lint
lint: ruff pyright ## Run all linters

.PHONY: test
test: ${VENV} ## Run tests
	${PYTEST} ${SRC_FILES}

.PHONY: ruff
ruff: ${VENV} ## Run ruff
	${RUFF} check ${SRC_FILES}

.PHONY: pyright
pyright: ${VENV} ## Run pyright
	${PYRIGHT} ${SRC_FILES}

.PHONY: check-readme
check-readme: ${VENV}  ## Check if readme is up to date
	$(MAKE) --no-print-directory --always-make README.md
	git diff --exit-code ':!uv.lock' || (echo "Run 'make README.md' and commit to fix" && exit 1)

README.md: ${SRC_FILES} docs/docs.md docs/fun.py
	cat docs/docs.md | ${PYTHON} -m mkdocs_fun_plugin docs/fun.py '{{(?P<func>[^\(]+)\((?P<params>[^\)]*)\)}}' '{{<!--\s*fun:disable\s*-->}}' '{{<!--\s*fun:enable\s*-->}}' > README.md || rm README.md

.PHONY: format
format: ${VENV} ## Run formatter
	${RUFF} format ${SRC_FILES}
	${RUFF} check --fix --force-exclude --select=I001 ${SRC_FILES}

.PHONY: build
build: ci ## Build package
	${UV} build

.PHONY: publish
publish: build ## Publish package
	${UV} publish
