#  -*- coding: utf-8 -*-
"""
Setuptools script for the pi-mqtt-gpio project.
"""

import os
from textwrap import fill, dedent

try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages


def required(fname):
    return open(
        os.path.join(
            os.path.dirname(__file__), fname
        )
    ).read().split('\n')


setup(
    name="pi_mqtt_gpio",
    version="0.0.3",
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
