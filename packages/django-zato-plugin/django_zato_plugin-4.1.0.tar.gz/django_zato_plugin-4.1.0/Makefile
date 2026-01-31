.PHONY: install build upload clean

install:
	uv sync
	uv build

build:
	uv build

upload:
	uv publish --token $(PYPI_TOKEN)

clean:
	rm -rf dist/ build/ *.egg-info src/*.egg-info .venv
