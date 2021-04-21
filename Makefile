.PHONY: docs

black:
	black -l 90 mqtt_io

clean:
	find mqtt_io -type d -name __pycache__ -prune -exec rm -rf {} \;
	rm -rf dist .eggs .mypy_cache .pytest_cache *.egg-info

graphs:
	dot -Tsvg -O interrupt_handling.dot
	dot -Tsvg -O interrupt_callbacks.dot

coverage:
	coverage run --source "." --omit "mqtt_io/tests/*,mqtt_io/modules/*" -m behave mqtt_io/tests/features -t ~skip
	coverage report -m

lint:
	pylint -d fixme mqtt_io
	mypy --show-error-codes --strict --no-warn-unused-ignores mqtt_io

build:
	poetry build

publish: build
	poetry publish

docs:
	poetry run python docs/generate_docs.py
