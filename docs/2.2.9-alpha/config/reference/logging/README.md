# logging :id=logging

Config to pass directly to
[Python's logging module](https://docs.python.org/3/library/logging.config.html#logging-config-dictschema)
to influence the logging output of the software.


```yaml
Type: dict
Required: False
Unlisted entries accepted: True
Default: {'version': 1, 'handlers': {'console': {'class': 'logging.StreamHandler', 'formatter': 'default', 'level': 'INFO'}}, 'formatters': {'default': {'format': '%(asctime)s %(name)s [%(levelname)s] %(message)s', 'datefmt': '%Y-%m-%d %H:%M:%S'}}, 'loggers': {'mqtt_io': {'level': 'INFO', 'handlers': ['console'], 'propagate': True}}}
```

