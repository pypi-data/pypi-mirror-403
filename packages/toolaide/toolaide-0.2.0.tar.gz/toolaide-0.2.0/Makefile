test:           ## Run unit tests
	pytest tests/ -v

test-llm:       ## Run LLM integration tests (requires running mlx-lm.server)
	@echo "Run manually: toolbox --workspace ."

install:        ## Install package in editable mode
	pip install -e .

install-dev:    ## Install with dev dependencies
	pip install -e ".[dev]"

build:          ## Build wheel package
	python -m build

publish-test:   ## Publish to TestPyPI
	twine upload --repository testpypi dist/*

publish:        ## Publish to PyPI
	twine upload dist/*
