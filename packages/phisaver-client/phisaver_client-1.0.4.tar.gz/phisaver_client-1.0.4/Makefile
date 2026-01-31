RUN = uv run

help:       ## Show this help.
		@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

buildtools:  ## Install development dependencies 
	uv pip install -e ".[dev]"

schema:
	@echo Run the following command to generate the schema:
	@echo pushd ../server/
	@echo make schema
	@echo popd


autogen: FORCE ## Generate the OpenAPI client code
		$(RUN) openapi-python-client generate --output-path src/ --overwrite --path ../server/schema.yml  --config openapi_python_client.yaml

runserver:   ## Run the django server
	@echo Run these commands
	@echo pushd ../server/
	@echo "make runserver &"
	@echo popd

clean-dist:  ## Clean build artifacts
	rm -rf dist/ build/ *.egg-info src/*.egg-info

build: buildtools clean-dist ## Build distribution packages
	$(RUN) python -m build

test-upload: build ## Upload to Test PyPI (test first!)
	@echo "Uploading to Test PyPI..."
	twine upload --repository testpypi dist/*
	@echo "Test with: pip install --index-url https://test.pypi.org/simple/ phisaver-client"

upload: build ## Upload to PyPI (PRODUCTION)
	@echo "WARNING: Publishing to PRODUCTION PyPI!"
	@echo "Version: $$(grep '^version' pyproject.toml | cut -d'"' -f2)"
	@read -p "Continue? [y/N] " confirm && [ "$$confirm" = "y" ]
	@echo "Uploading to PyPI..."
	twine upload dist/*
	@echo "Published! Install with: pip install phisaver-client"

check-version: ## Show current version
	@grep '^version' pyproject.toml

FORCE: ## Force the rule to always run
	@true
		
