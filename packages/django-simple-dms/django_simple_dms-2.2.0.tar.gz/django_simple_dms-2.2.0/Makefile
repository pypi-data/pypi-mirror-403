BUILDDIR='.build'
PYTHONPATH:=${PWD}/tests/:${PWD}:${PYTHONPATH}
BUILDDIR?=./.build
CURRENT_BRANCH:=$(shell git rev-parse --abbrev-ref HEAD)
NODE_ENV?=production
.PHONY: help runonce run i18n
.DEFAULT_GOAL := help

ifeq ($(wildcard .python-version),)
    PYTHON_VERSION = ""
else
    PYTHON_VERSION = $(shell head -1 .python-version)
endif

ifeq ($(wildcard .initialized),)
    INITIALIZED = 0
else
    INITIALIZED = 1
endif

guard-%:
	@if [ "${${*}}" = "" ]; then \
		echo "Environment variable $* not set"; \
        exit 1; \
    fi


define BROWSER_PYSCRIPT
import os, webbrowser, sys

from urllib.request import pathname2url

webbrowser.open("file://" + pathname2url(os.path.abspath(sys.argv[1])))
endef
export BROWSER_PYSCRIPT

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z0-9_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

BROWSER := python -c "$$BROWSER_PYSCRIPT"

help:
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

.mkbuilddir:
	@mkdir -p ${BUILDDIR}


backup_file := ~$(shell date +%Y-%m-%d).json
reset-migrations: ## reset django migrations
	./manage.py check
	find src -name '0*[1,2,3,4,5,6,7,8,9,0]*' | xargs rm -f
	rm -f *.db
	./manage.py makemigrations django_simple_dms
	./manage.py makemigrations --check
	@echo "\033[31;1m You almost there:"
	@echo "\033[37;1m  - run ./manage.py upgrade --no-input"
	@echo "\033[37;1m  - run ./manage.py demo --no-input"


lint:  ## code lint
	pre-commit run --all-files

clean: ## clean development tree
	rm -fr ${BUILDDIR} build dist src/*.egg-info .coverage coverage.xml .eggs .pytest_cache *.egg-info
	find src -name __pycache__ -o -name "*.py?" -o -name "*.orig" -prune | xargs rm -rf
	find tests -name __pycache__ -o -name "*.py?" -o -name "*.orig" -prune | xargs rm -rf
	find src/_other_/locale -name django.mo | xargs rm -f

fullclean:
	rm -fr .tox .cache .venv node_modules
	$(MAKE) clean

test:
	pytest tests/

.init-db:
	sh tools/dev/initdb.sh

.zap-migrations_:
	@if [ "`find src -name "0*.py" | grep "/migrations/"`" != "" ]; then \
       rm `find src -name "0*.py" | grep "/migrations/"` ; \
    fi
#	@./manage.py makemigrations

.upgrade:
	./manage.py upgrade -vv


.zap: .init-db .upgrade .loaddata

.zap-migrations: .zap-migrations_ .zap  ## Destroys and recreate migrations

test-fast: ## runtest integration and unit tests in parallel
	@pytest -n auto -m "selenium or not selenium" --no-cov

test-cov: ## run tests with coverage
	@pytest -m "selenium or not selenium" tests --create-db --junitxml=`pwd`/~build/pytest.xml -vv \
        --cov-report=xml:`pwd`/~build/coverage.xml --cov-report=html --cov-report=term \
        --cov-config=tests/.coveragerc \
        --cov=krm3
	@if [ "${BROWSERCMD}" != "" ]; then \
    	${BROWSERCMD} `pwd`/~build/coverage/index.html ; \
    fi

run:  ## Run a Django development webserver (assumes that `runonce` was previously run).
	npm run build
	./manage.py runserver


detect-secrets:  ## Scanning secrets or adding New Secrets to Baseline
	@if [ ! -f ".secrets.baseline" ]; then \
  		echo "Initialising secrets" ; \
		detect-secrets scan > .secrets.baseline ; \
	fi
	@detect-secrets scan --baseline .secrets.baseline

outdated:  ## Generates .outdated.txt and .tree.txt files
	uv tree > .tree.txt
	uv pip list --outdated > .outdated.txt

compilemessages:
	@./manage.py compilemessages -i .tox -i .venv
