# from https://github.com/audreyfeldroy/cookiecutter-pypackage
define BROWSER_PYSCRIPT
import os, webbrowser, sys
from urllib.request import pathname2url
webbrowser.open("file://" + pathname2url(os.path.abspath(sys.argv[1])))
endef
export BROWSER_PYSCRIPT
BROWSER := python -c "$$BROWSER_PYSCRIPT"

define PRINT_HELP_PYSCRIPT
import re, sys
for line in sys.stdin:
	match = re.match(r'^[.]PHONY: (\w+).*?#\s*(.*)', line)
	if match:
		print(f"{match.group(1):20}{match.group(2)}")
endef
export PRINT_HELP_PYSCRIPT

# Default target
.PHONY: help
help:
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

.PHONY: test # Run pytest and mypy
test:
	pytest
	mypy --install-types --non-interactive --check-untyped-defs src/jwlib tests

.PHONY: coverage # Create test coverage report
coverage:
	coverage run -m pytest
	coverage html
	$(BROWSER) htmlcov/index.html

.PHONY: record # Record missing HTTP requests needed by pytest
record:
	pytest --record-mode=new_episodes

.PHONY: record-all # Re-record all HTTP requests needed by pytest
record-all:
	rm tests/cassettes/test_media/cassette.yaml
	pytest --record-mode=new_episodes

.PHONY: docs # Build documentation
docs:
	sphinx-build -M clean docs docs/_build
	sphinx-build -M html docs docs/_build

.PHONY: watchdocs # Re-build documentation whenever it changes
watchdocs: docs
	$(BROWSER) docs/_build/html/index.html
	watchmedo shell-command --recursive --patterns '*.rst;*.py' --ignore-directories . --command 'make docs'
