black:
	black -l 90 mqtt_io

packages: clean schema sdist wheel2 wheel3

sdist: schema
	python setup.py sdist

wheel3: schema
	python3 setup.py bdist_wheel

clean:
	find pi_mqtt_gpio -type d -name __pycache__ -prune -exec rm -rf {} \;
	rm -rf dist .eggs .mypy_cache .pytest_cache *.egg-info

upload: packages
	twine upload dist/*
	$(MAKE) clean

graphs:
	dot -Tsvg -O interrupt_handling.dot
	dot -Tsvg -O interrupt_callbacks.dot

coverage:
	coverage run --source "." --omit "mqtt_io/tests/*,mqtt_io/modules/*" -m behave mqtt_io/tests/features
	coverage report -m

requirements:
	poetry export > requirements.txt
	echo "hbmqtt==0.9.6" >> requirements.txt

lint:
	pylint -d fixme mqtt_io
	mypy --show-error-codes --strict --no-warn-unused-ignores mqtt_io

publish:
	sed -i "s/# hbmqtt/hbmqtt/" pyproject.toml
	poetry build
	poetry publish
	sed -i "s/hbmqtt/# hbmqtt/" pyproject.toml
