import yaml

CONFIG_SCHEMA = yaml.safe_load("""
mqtt:
  type: dict
  required: yes
  schema:
    host:
      type: string
      empty: no
      required: no
      default: localhost
    port:
      type: integer
      min: 1
      max: 65535
      required: no
      default: 1883
    user:
      type: string
      required: no
      default: ""
    password:
      type: string
      required: no
      default: ""
    client_id:
      type: string
      required: no
      default: ""
    topic_prefix:
      type: string
      required: no
      default: ""
      coerce: rstrip_slash
    protocol:
      type: string
      required: no
      empty: no
      coerce: tostring
      default: "3.1.1"
      allowed:
        - "3.1"
        - "3.1.1"
    status_topic:
      type: string
      required: no
      default: status
    status_payload_running:
      type: string
      required: no
      default: running
    status_payload_stopped:
      type: string
      required: no
      default: stopped
    status_payload_dead:
      type: string
      required: no
      default: dead
    tls:
      type: dict
      required: no
      schema:
        enabled:
          type: boolean
          required: yes
        ca_certs:
          type: string
          required: no
        certfile:
          type: string
          required: no
        keyfile:
          type: string
          required: no
        cert_reqs:
          type: string
          required: no
          allowed:
            - CERT_NONE
            - CERT_OPTIONAL
            - CERT_REQUIRED
          default: CERT_REQUIRED
        tls_version:
          type: string
          required: no
        ciphers:
          type: string
          required: no
        insecure:
          type: boolean
          required: no
          default: false

gpio_modules:
  type: list
  required: no
  default: []
  schema:
    type: dict
    allow_unknown: yes
    schema:
      name:
        type: string
        required: yes
        empty: no
      module:
        type: string
        required: yes
        empty: no
      cleanup:
        type: boolean
        required: no
        default: yes

sensor_modules:
  type: list
  required: no
  default: []
  schema:
    type: dict
    allow_unknown: yes
    schema:
      name:
        type: string
        required: yes
        empty: no
      module:
        type: string
        required: yes
        empty: no
      cleanup:
        type: boolean
        required: no
        default: yes

digital_inputs:
  type: list
  required: no
  default: []
  schema:
    type: dict
    schema:
      name:
        type: string
        required: yes
        empty: no
      module:
        type: string
        required: yes
        empty: no
      pin:
        type:
          - string
          - integer
        required: yes
        empty: no
      on_payload:
        type: string
        required: no
        default: "ON"
      off_payload:
        type: string
        required: no
        default: "OFF"
      interrupt_payload:
        type: string
        required: no
        default: "INT"
      pullup:
        type: boolean
        required: no
        default: no
      pulldown:
        type: boolean
        required: no
        default: no
      interrupt:
        type: string
        required: no
        default: none
        allowed:
          - rising
          - falling
          - both
          - none
      bouncetime:
        type: integer
        required: no
        default: 100
        min: 1
      retain:
        type: boolean
        required: no
        default: no

digital_outputs:
  type: list
  required: no
  default: []
  schema:
    type: dict
    schema:
      name:
        type: string
        required: yes
      module:
        type: string
        required: yes
      pin:
        type:
          - string
          - integer
        required: yes
        empty: no
      on_payload:
        type: string
        required: no
        empty: no
      off_payload:
        type: string
        required: no
        empty: no
      inverted:
        type: boolean
        required: no
        default: no
      initial:
        type: string
        required: no
        allowed:
          - high
          - low
      timed_set_ms:
        type: integer
        required: no
        empty: yes
      retain:
        type: boolean
        required: no
        default: no

sensor_inputs:
  type: list
  required: no
  default: []
  schema:
    type: dict
    allow_unknown: yes
    schema:
      name:
        type: string
        required: yes
        empty: no
      module:
        type: string
        required: yes
        empty: no
      retain:
        type: boolean
        required: no
        default: no
      interval:
        type: integer
        required: no
        default: 60
        min: 1
      digits:
        type: integer
        required: no
        default: 2
        min: 0

logging:
  type: dict
  required: no
  allow_unknown: yes
  default:
    version: 1
    formatters:
      simple:
        format: "%(asctime)s %(name)s (%(levelname)s): %(message)s"
    handlers:
      console:
        class: logging.StreamHandler
        level: DEBUG
        formatter: simple
        stream: ext://sys.stdout
    loggers:
      mqtt_gpio:
        level: INFO
        handlers: [console]
        propagate: yes

""")
