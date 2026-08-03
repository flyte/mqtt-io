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

## Platform & Sensor-specific Docker Config

These are provided as examples, and may apply more generally than the Sensors & Platforms mentioned here.

### DHT22 on Raspberry Pi

#### GPIO Device Filesystem Permissions
In addition to the `/dev/gpiomem` device being passed through to the Docker Container, 
`mqtt_io` also needs permission to use the device.

By default, on Raspberry Pi OS, access to the GPIO is granted by membership of the `gpio` group.

You can run the command `grep gpio /etc/group` to find the GID (group ID) of the `gpio` group. Here it is `993`;
```
$ grep gpio /etc/group
gpio:x:993:pi
```

To add the User inside the `mqtt_io` Docker container to this group, add it on the command line:
```
docker run -ti --rm -v /path/to/your/config.yml:/config.yml --device /dev/gpiomem --group-add 993 flyte/mqtt-io
```

Or in a `docker-compose.yml` file:
```
services:
  mqtt-io:
    image: flyte/mqtt-io
    group_add:
      - 993
```

#### RPi.GPIO Library Dependencies
The DHT22 Sensor Module relies on the `RPi.GPIO` library to use the GPIO on a Raspberry Pi.
This library performs some checks on import to check that it is being run on a Raspberry Pi.
To pass these checks, the Docker Container needs to be configured with;
* Access to the `/dev/gpiomem` device, to check that GPIO is accessible
* Access to the `/proc/device-tree/system/linux,revision` `procfs` "file", to check that it is running on a Raspberry Pi

Access to the Host `/proc` filesystem can be given to the Container with the `security_opt` of `systempaths=unconfined`.

On the command line, this uses the flag:
```
--security-opt="systempaths=unconfined"
```

Or for `docker-compose.yml`, add the following to the service entry:
```
security_opt:
  - systempaths=unconfined
```

!> `systempaths=unconfined` will give the Container access to all of `/proc` & `/sys`. 
Filesystem permissions still apply, but if these are circumvented the Container can edit values in `/proc` & `/sys`

_Please raise an issue on Github if you find that any of this information is incorrect._
