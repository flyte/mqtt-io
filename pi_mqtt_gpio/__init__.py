import yaml, os

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

CONFIG_SCHEMA = yaml.safe_load(read('../config.schema.yml'))
