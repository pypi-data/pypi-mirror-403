.PHONY: help install dev-install test lint format clean build

help:
	@echo "Tallyfy SDK Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install          Install package dependencies"
	@echo "  make dev-install      Install package with dev dependencies"
	@echo ""
	@echo "Development:"
	@echo "  make test            Run tests"
	@echo "  make lint            Run linters (flake8, mypy)"
	@echo "  make format          Format code with black"
	@echo "  make clean           Remove build artifacts"
	@echo "  make build           Build distribution packages"
	@echo ""
	@echo "Release:"
	@echo "  Use GitHub Actions to create releases"
	@echo "  https://github.com/tallyfy/sdk/actions"
	@echo ""

install:
	pip install -e .

dev-install:
	pip install -e ".[dev]"

test:
	pytest tests/ -v

lint:
	flake8 tallyfy/
	mypy tallyfy/

format:
	black tallyfy/ tests/

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf tallyfy.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: clean
	python -m build
