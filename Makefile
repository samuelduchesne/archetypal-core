.PHONY: install
install: ## Install the poetry environment and install the pre-commit hooks
	@echo "🚀 Creating virtual environment using pyenv and poetry"
	@poetry env use 3.12
	@poetry install
	@poetry run pre-commit install
	@poetry shell

.PHONY: check
check: ## Run code quality tools.
	@echo "🚀 Checking Poetry lock file consistency with 'pyproject.toml': Running poetry check --lock"
	@poetry check --lock
	@echo "🚀 Linting code: Running pre-commit"
	@poetry run pre-commit run -a
	@echo "🚀 Static type checking: Running pyright"
	@poetry run pyright
	@echo "🚀 Checking for obsolete dependencies: Running deptry"
	@poetry run deptry .

.PHONY: test
test: ## Test the code with pytest
	@echo "🚀 Testing code: Running pytest"
	@poetry run pytest --cov --cov-config=pyproject.toml --cov-report=xml

.PHONY: build
build: clean-build ## Build wheel file using poetry
	@echo "🚀 Creating wheel file"
	@poetry build
	@echo "🚀 Building Rust code"
	@cd archetypal_core/rust && cargo build --release

.PHONY: clean-build
clean-build: ## clean build artifacts
	@rm -rf dist
	@rm -rf archetypal_core/rust/target

.PHONY: publish
publish: ## publish a release to pypi.
	@echo "🚀 Publishing: Dry run."
	@poetry config pypi-token.pypi $(PYPI_TOKEN)
	@poetry publish --dry-run
	@echo "🚀 Publishing."
	@poetry publish

.PHONY: build-and-publish
build-and-publish: build publish ## Build and publish.

.PHONY: docs-test
docs-test: ## Test if documentation can be built without warnings or errors
	@poetry run mkdocs build -s

.PHONY: docs
docs: ## Build and serve the documentation
	@poetry run mkdocs serve

.PHONY: generate
generate:
	@echo "Running Datamodel Code Generator..."
	@datamodel-codegen --input archetypal_core/schema.json \
		--input-file-type jsonschema \
		--use-non-positive-negative-number-constrained-types \
		--empty-enum-field-name Empty \
		--use-annotated \
		--enum-field-as-literal all \
		--field-constraints \
		--use-standard-collections \
		--use-union-operator \
		--class-name IDF \
		--field-extra-keys units legacy_idd \
		--target-python-version 3.11 \
		--use-schema-description \
		--reuse-model \
		--collapse-root-models \
		--disable-appending-item-suffix \
		--output-model-type pydantic_v2.BaseModel \
		--use-exact-imports \
		--output ./archetypal_core/automodels.py

.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
