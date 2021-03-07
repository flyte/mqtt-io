# Deployment using Supervisor

MQTT IO is not tied to any specific deployment method, but one recommended way is to use `virtualenv` and `supervisor`. This will launch the project at boot time and handle restarting and log file rotation. It's quite simple to set up:

If using Raspbian, install `supervisor` with `apt`.

```bash
sudo apt-get update
sudo apt-get install supervisor
```

Not strictly necessary, but it's recommended to install the project into a [virtualenv](http://docs.python-guide.org/en/latest/dev/virtualenvs/#lower-level-virtualenv).

```bash
sudo apt-get install python-venv
cd /home/pi
python3 -m venv ve
. ve/bin/activate
pip install mqtt-io
```

Create yourself a config file, following instructions and examples above, and save it somewhere, such as `/home/pi/mqtt-io.yml`.

Create a [supervisor config file](http://supervisord.org/configuration.html#program-x-section-settings) in /etc/supervisor/conf.d/mqtt-io.conf something along the lines of the following:

```ini
[program:mqtt_io]
command = /home/pi/ve/bin/python -m mqtt_io mqtt-io.yml
directory = /home/pi
redirect_stderr = true
stdout_logfile = /var/log/mqtt-io.log
```

Save the file and then run the following to update supervisor and start the program running.

```bash
sudo supervisorctl update
```

Check the status of your new supervisor job:

```bash
sudo supervisorctl status
```

Check the [supervisor docs](http://supervisord.org/running.html#supervisorctl-command-line-options) for more `supervisorctl` commands.
