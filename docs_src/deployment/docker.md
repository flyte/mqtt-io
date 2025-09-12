# Deployment with Docker

_Current state: experimental and unmaintained_

GitHub CI is used to build multi-arch Docker Images for the following Platforms & CPU Archictures:
* `linux/amd64` - e.g. AMD & Intel x86_64 CPUs
* `linux/arm/v7` - e.g. Older Raspberry Pis with 32-bit ARM Cores, or newer Pis running a 32-bit OS
* `linux/arm64` - e.g. Newer Raspberry Pis with 64-bit ARM Cores running a 64-bit OS

Images for all Platforms & CPU Architectures are available under the same name of `flyte/mqtt-io`. Docker will generally detect the CPU Architecture on the current system and download the appropriate Image.

To run this software using Docker, create a config file as described for running outside of Docker and run with Docker:

```
docker run -ti --rm -v /path/to/your/config.yml:/config.yml flyte/mqtt-io
```

Or to run in the background:

```
docker run -d --name mqtt-io -v /path/to/your/config.yml:/config.yml flyte/mqtt-io
```

You'll most likely want to use some hardware devices in your config, since that's what this project is all about. For example, if you wish to use the i2c bus, pass it through with a `--device` parameter:

```
docker run -ti --rm -v /path/to/your/config.yml:/config.yml --device /dev/i2c-0 flyte/mqtt-io
```

If you aren't able to find the exact device path to use, then you can also run the docker container in `--privileged` mode which will pass all of the devices through from the host:

```
docker run -ti --rm -v /path/to/your/config.yml:/config.yml --privileged flyte/mqtt-io
```

_Please raise an issue on Github if you find that any of this information is incorrect._
