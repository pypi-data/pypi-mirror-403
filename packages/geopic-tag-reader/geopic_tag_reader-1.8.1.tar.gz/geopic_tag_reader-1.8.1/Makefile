.DEFAULT_GOAL := help

.PHONY: docs test type-check fmt ci

prepare_release: i18n-code2pot i18n-po2code docs ci

test: ## Run tests
	pytest

type-check: ## Check all python types
	mypy geopic_tag_reader/

fmt: ## Format code
	python -m black --fast .

ci: type-check fmt test ## Run all check like the ci

docs:  ## Generates documentation from Typer embedded docs
	python -m typer ./geopic_tag_reader/main.py utils docs --name geopic-tag-reader --output docs/tech/cli.md

help: ## Print this help message
	@grep -E '^[a-zA-Z_-]+:.*## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

#############################
# Internationalization
#

# Extract labels from Python code into POT catalog
i18n-code2pot:
	xgettext -d geopic_tag_reader -o geopic_tag_reader/translations/geopic_tag_reader.pot geopic_tag_reader/*.py
	msginit --locale=en --no-translator --input=geopic_tag_reader/translations/geopic_tag_reader.pot --output=geopic_tag_reader/translations/en/LC_MESSAGES/geopic_tag_reader.po

# Transform all PO translated files into MO for Python to use them
SOURCES=$(wildcard geopic_tag_reader/translations/**/LC_MESSAGES/*.po)
TARGETS=$(SOURCES:.po=.mo)
i18n-po2code: $(TARGETS)
%.mo: %.po
	msgfmt $< -o $@
