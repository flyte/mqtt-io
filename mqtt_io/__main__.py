"""
Main entrypoint when MQTT IO is invoked as `python -m mqtt_io`.
"""

import argparse
import logging.config
import sys

from .config import load_main_config
from .exceptions import ConfigValidationFailed
from .server import MqttIo


def main() -> None:
    """
    Main entrypoint function.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("config")
    args = parser.parse_args()

    # Load, validate and normalise config, or quit.
    try:
        config = load_main_config(args.config)
    except ConfigValidationFailed as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)

    if config["logging"]:
        logging.config.dictConfig(config["logging"])

    mqtt_gpio = MqttIo(config)
    mqtt_gpio.run()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("")
