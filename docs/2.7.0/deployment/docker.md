# Deployment with Docker

_Current state: experimental and unmaintained_

Two images have been created for Docker. One using the x86_64 architecture (for Intel and AMD CPUs) and one for the ARM architecture (for Raspberry Pi etc.). The tags of the images are therefore `flyte/mqtt-gpio:x86_64` and `flyte/mqtt-gpio:armv7l`. These are the outputs of `uname -m` on the two platforms they've been built on. For the following examples I'll assume you're running on Raspberry Pi.

You may also run this software using Docker. You must create your config file as above, then run the docker image:

```
docker run -ti --rm -v /path/to/your/config.yml:/config.yml flyte/mqtt-gpio:armv7l
```

Or to run in the background:

```
docker run -d --name mqtt-gpio -v /path/to/your/config.yml:/config.yml flyte/mqtt-gpio:armv7l
```

You'll most likely want to use some hardware devices in your config, since that's what this project is all about. For example, if you wish to use the i2c bus, pass it through with a `--device` parameter:

```
docker run -ti --rm -v /path/to/your/config.yml:/config.yml --device /dev/i2c-0 flyte/mqtt-gpio:armv7l
```

If you aren't able to find the exact device path to use, then you can also run the docker container in `--privileged` mode which will pass all of the devices through from the host:

```
docker run -ti --rm -v /path/to/your/config.yml:/config.yml --privileged flyte/mqtt-gpio:armv7l
```

_Please raise an issue on Github if you find that any of this information is incorrect._
