.PHONY: install shell publish test test-verbose clean

install:
	uv sync --dev

shell:
	uv run python -m loopy.shell

test:
	uv run pytest

test-verbose:
	uv run pytest -vv

publish:
	rm -rf dist
	uv build
	uv run twine upload --repository pypi dist/loopy_fs-*

clean:
	rm -rf dist
	find . -name "__pycache__" -type d -prune -exec rm -rf {} +
