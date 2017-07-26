import yaml

CONFIG_SCHEMA = yaml.load("""
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

gpio_modules:
  type: list
  required: yes
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
        type: integer
        required: yes
        min: 0
      on_payload:
        type: string
        required: yes
        empty: no
      off_payload:
        type: string
        required: yes
        empty: no
      pullup:
        type: boolean
        required: no
        default: no
      pulldown:
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
        type: integer
        required: yes
        min: 0
      on_payload:
        type: string
        required: no
        empty: no
      off_payload:
        type: string
        required: no
        empty: no
""")
