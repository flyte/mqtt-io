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
	poetry run coverage run --source "." --omit "mqtt_io/tests/*,mqtt_io/modules/*" -m behave mqtt_io/tests/features -t ~skip
	poetry run coverage report -m

lint:
	poetry run pylint -d fixme mqtt_io
	poetry run mypy --show-error-codes --strict --no-warn-unused-ignores mqtt_io

build:
	poetry build

publish: build
	poetry publish --build

docs:
	poetry run python docs_src/generate_docs.py

docker:
	docker buildx build --platform linux/arm/v7,linux/arm64/v8,linux/amd64 -t flyte/mqtt-io:`git rev-parse --short HEAD` --push --build-arg BUILDX_QEMU_ENV=true .

qemu_reset:
	# https://github.com/docker/buildx/issues/495
	docker pull multiarch/qemu-user-static
	docker run --rm --privileged multiarch/qemu-user-static --reset -p yes
	echo "If this next step fails then you may need to 'docker buildx rm multiarch' first"
	docker buildx create --name multiarch --driver docker-container --use
	docker buildx inspect --bootstrap
