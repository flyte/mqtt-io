#  -*- coding: utf-8 -*-
"""
Setuptools script for the pi-mqtt-gpio project.
"""

import os
from textwrap import fill, dedent
from string import Template
from distutils.core import Command


try:
    from setuptools import setup, find_packages
    from setuptools.command.build_py import build_py
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages
    from setuptools.command.build_py import build_py


def required(fname):
    return open(
        os.path.join(
            os.path.dirname(__file__), fname
        )
    ).read().split('\n')


class SchemaCommand(Command):
    user_options = []

    def run(self):
        if self.dry_run:
            return

        with open("pi_mqtt_gpio/__init__.py.template") as f_templ:
            templ = Template(f_templ.read())
        with open("config.schema.yml") as f_schema:
            with open("pi_mqtt_gpio/__init__.py", "w") as f_out:
                f_out.write(templ.substitute(config_schema=f_schema.read()))
                f_out.flush()

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass


setup(
    name="pi_mqtt_gpio",
    version="0.2.1",
    cmdclass={"insert_schema": SchemaCommand},
    packages=find_packages(
        exclude=[
            "*.tests",
            "*.tests.*",
            "tests.*",
            "tests",
            "*.ez_setup",
            "*.ez_setup.*",
            "ez_setup.*",
            "ez_setup",
            "*.examples",
            "*.examples.*",
            "examples.*",
            "examples"
        ]
    ),
    scripts=[],
    entry_points={
        "console_scripts": [
            "pi_mqtt_gpio = pi_mqtt_gpio.__main__:main"
        ]
    },
    include_package_data=True,
    setup_requires='pytest-runner',
    tests_require='pytest',
    install_requires=required('requirements.txt'),
    test_suite='pytest',
    zip_safe=False,
    # Metadata for upload to PyPI
    author='Ellis Percival',
    author_email="pi_mqtt_gpio@failcode.co.uk",
    description=fill(dedent("""\
        Expose the Raspberry Pi GPIO pins (and/or external IO modules such as the PCF8574) to an
        MQTT server. This allows pins to be read and switched by reading or writing messages to
        MQTT topics.
    """)),
    classifiers=[
        "Programming Language :: Python",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Topic :: Communications",
        "Topic :: Home Automation",
        "Topic :: System :: Networking"
    ],
    license="MIT",
    keywords="",
    url="https://github.com/flyte/pi-mqtt-gpio"
)
