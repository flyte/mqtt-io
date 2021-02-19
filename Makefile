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
