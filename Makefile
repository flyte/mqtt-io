schema:
	python setup.py insert_schema

packages: clean schema sdist wheel2 wheel3

sdist: schema
	python setup.py sdist

wheel2: schema
	python2 setup.py bdist_wheel

wheel3: schema
	python3 setup.py bdist_wheel

clean:
	cp pi_mqtt_gpio/__init__.py.die pi_mqtt_gpio/__init__.py
	rm -rf .cache .eggs build *.egg-info
	find pi_mqtt_gpio -type d -name __pycache__ -prune -exec rm -rf {} \;
	rm -rf dist

upload: packages
	twine upload dist/*
	$(MAKE) clean
