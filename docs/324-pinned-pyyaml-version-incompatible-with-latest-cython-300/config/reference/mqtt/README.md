# mqtt :id=mqtt

Contains the configuration data used for connecting to an MQTT server.


```yaml
Type: dict
Required: True
```

**Example**:

```yaml
mqtt:
  host: test.mosquitto.org
  port: 8883
  topic_prefix: mqtt_io
  ha_discovery:
    enabled: yes
  tls:
    enabled: yes
    ca_certs: mosquitto.org.crt
    certfile: client.crt
    keyfile: client.key
```

## host :id=mqtt-host

*mqtt*.**host**

Host name or IP address of the MQTT server.

```yaml
Type: string
Required: True
```

## port :id=mqtt-port

*mqtt*.**port**

Port number to connect to on the MQTT server.

```yaml
Type: integer
Required: False
Default: 1883
```

## user :id=mqtt-user

*mqtt*.**user**

Username to authenticate with on the MQTT server.

```yaml
Type: string
Required: False
Default: 
```

## password :id=mqtt-password

*mqtt*.**password**

Password to authenticate with on the MQTT server.

```yaml
Type: string
Required: False
Default: 
```

## client_id :id=mqtt-client_id

*mqtt*.**client_id**

[MQTT client ID](https://www.cloudmqtt.com/blog/2018-11-21-mqtt-what-is-client-id.html) to use on the MQTT server.


```yaml
Type: string
Required: False
Default: 
```

## topic_prefix :id=mqtt-topic_prefix

*mqtt*.**topic_prefix**

Prefix to use for all topics.

```yaml
Type: string
Required: False
Default: 
```

?> For example, a `topic_prefix` of `home/livingroom` would make a digital input
called "doorbell" publish its changes to the `home/livingroom/input/doorbell`
topic.


## clean_session :id=mqtt-clean_session

*mqtt*.**clean_session**

Whether or not to start a
[clean MQTT session](https://www.hivemq.com/blog/mqtt-essentials-part-7-persistent-session-queuing-messages/)
on every MQTT connection.


```yaml
Type: boolean
Required: False
Default: False
```

## protocol :id=mqtt-protocol

*mqtt*.**protocol**

Version of the MQTT protocol to use.

```yaml
Type: string
Required: False
Allowed: ['3.1', '3.1.1']
Default: 3.1.1
```

?> This renders in the documentation as a float, but should always be set within quotes.


## keepalive :id=mqtt-keepalive

*mqtt*.**keepalive**

How frequently in seconds to send
[ping packets](https://www.hivemq.com/blog/mqtt-essentials-part-10-alive-client-take-over/)
to the MQTT server.


```yaml
Type: integer
Required: False
Unit: seconds
Default: 10
```

## status_topic :id=mqtt-status_topic

*mqtt*.**status_topic**

Topic on which to send messages about the running status of this software.

```yaml
Type: string
Required: False
Default: status
```

?> Sends the payloads configured in `status_payload_running`,
`status_payload_stopped` and `status_payload_dead`.


## status_payload_running :id=mqtt-status_payload_running

*mqtt*.**status_payload_running**

Payload to send on the status topic when the software is running.

```yaml
Type: string
Required: False
Default: running
```

## status_payload_stopped :id=mqtt-status_payload_stopped

*mqtt*.**status_payload_stopped**

Payload to send on the status topic when the software has exited cleanly.

```yaml
Type: string
Required: False
Default: stopped
```

## status_payload_dead :id=mqtt-status_payload_dead

*mqtt*.**status_payload_dead**

Payload to send on the status topic when the software has exited unexpectedly.

```yaml
Type: string
Required: False
Default: dead
```

?> Uses [MQTT Last Will and Testament](https://www.hivemq.com/blog/mqtt-essentials-part-9-last-will-and-testament/)
to make the server automatically send this payload if our connection fails.


## client_module :id=mqtt-client_module

*mqtt*.**client_module**

MQTT Client implementation module path.

```yaml
Type: string
Required: False
Default: mqtt_io.mqtt.asyncio_mqtt
```

?> There's currently only one implementation, which uses the
[asyncio-mqtt](https://github.com/sbtinstruments/asyncio-mqtt/) client.


## ha_discovery :id=mqtt-ha_discovery

*mqtt*.**ha_discovery**

```yaml
Type: dict
Required: False
```

### enabled :id=mqtt-ha_discovery-enabled

*mqtt.ha_discovery*.**enabled**

Enable [Home Assistant MQTT discovery](https://www.home-assistant.io/docs/mqtt/discovery/)
of our configured devices.


```yaml
Type: boolean
Required: True
```

### prefix :id=mqtt-ha_discovery-prefix

*mqtt.ha_discovery*.**prefix**

Prefix for the Home Assistant MQTT discovery topic.

```yaml
Type: string
Required: False
Default: homeassistant
```

### name :id=mqtt-ha_discovery-name

*mqtt.ha_discovery*.**name**

Name to identify this "device" in Home Assistant.

```yaml
Type: string
Required: False
Default: MQTT IO
```

## tls :id=mqtt-tls

*mqtt*.**tls**

TLS/SSL settings for connecting to the MQTT server over an encrypted connection.


```yaml
Type: dict
Required: False
```

**Example**:

```yaml
mqtt:
  host: localhost
  tls:
    enabled: yes
    ca_certs: mosquitto.org.crt
    certfile: client.crt
    keyfile: client.key
```

### enabled :id=mqtt-tls-enabled

*mqtt.tls*.**enabled**

Enable a secure connection to the MQTT server.

```yaml
Type: boolean
Required: True
```

?> Most of these options map directly to the
[`tls_set()` arguments](https://www.eclipse.org/paho/index.php?page=clients/python/docs/index.php#tls-set)
on the Paho MQTT client.


### ca_certs :id=mqtt-tls-ca_certs

*mqtt.tls*.**ca_certs**

Path to the Certificate Authority certificate files that are to be treated
as trusted by this client.
[More info](https://www.eclipse.org/paho/index.php?page=clients/python/docs/index.php#tls-set)


```yaml
Type: string
Required: False
```

### certfile :id=mqtt-tls-certfile

*mqtt.tls*.**certfile**

Path to the PEM encoded client certificate.
[More info](https://www.eclipse.org/paho/index.php?page=clients/python/docs/index.php#tls-set)


```yaml
Type: string
Required: False
```

### keyfile :id=mqtt-tls-keyfile

*mqtt.tls*.**keyfile**

Path to the PEM encoded client private key.
[More info](https://www.eclipse.org/paho/index.php?page=clients/python/docs/index.php#tls-set)


```yaml
Type: string
Required: False
```

### cert_reqs :id=mqtt-tls-cert_reqs

*mqtt.tls*.**cert_reqs**

Defines the certificate requirements that the client imposes on the MQTT server.
[More info](https://www.eclipse.org/paho/index.php?page=clients/python/docs/index.php#tls-set)


```yaml
Type: string
Required: False
Allowed: ['CERT_NONE', 'CERT_OPTIONAL', 'CERT_REQUIRED']
Default: CERT_REQUIRED
```

?> By default this is `CERT_REQUIRED`, which means that the broker must provide a certificate.


### tls_version :id=mqtt-tls-tls_version

*mqtt.tls*.**tls_version**

Specifies the version of the SSL/TLS protocol to be used.
[More info](https://www.eclipse.org/paho/index.php?page=clients/python/docs/index.php#tls-set)


```yaml
Type: string
Required: False
```

?> By default the highest TLS version is detected.


### ciphers :id=mqtt-tls-ciphers

*mqtt.tls*.**ciphers**

Which encryption ciphers are allowable for this connection.
[More info](https://www.eclipse.org/paho/index.php?page=clients/python/docs/index.php#tls-set)


```yaml
Type: string
Required: False
```

### insecure :id=mqtt-tls-insecure

*mqtt.tls*.**insecure**

Configure verification of the server hostname in the server certificate.
[More info](https://www.eclipse.org/paho/index.php?page=clients/python/docs/index.php#tls-insecure-set)


```yaml
Type: boolean
Required: False
Default: False
```

?> If set to true, it is impossible to guarantee that the host you are
connecting to is not impersonating your server. This can be useful in
initial server testing, but makes it possible for a malicious third party
to impersonate your server through DNS spoofing, for example.
Do not use this function in a real system. Setting value to true means there
is no point using encryption.


## reconnect_delay :id=mqtt-reconnect_delay

*mqtt*.**reconnect_delay**

Time in seconds to wait between reconnect attempts.


```yaml
Type: integer
Required: False
Default: 2
```

## reconnect_count :id=mqtt-reconnect_count

*mqtt*.**reconnect_count**

Max number of retries of connections before giving up and exiting.
Null value means infinite reconnects (default).
The counter is reset when the connection is reestablished successfully.


```yaml
Type: integer
Required: False
Default: None
```

