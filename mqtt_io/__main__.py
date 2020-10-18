import logging.config
import argparse
import sys

from .config import load_main_config
from .exceptions import ConfigValidationFailed
from .server import MqttGpio


def main():
    p = argparse.ArgumentParser()
    p.add_argument("config")
    args = p.parse_args()

    # Load, validate and normalise config, or quit.
    try:
        config = load_main_config(args.config)
    except ConfigValidationFailed as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

    if config["logging"]:
        logging.config.dictConfig(config["logging"])

    mqtt_gpio = MqttGpio(config)
    mqtt_gpio.run()


if __name__ == "__main__":
    main()
