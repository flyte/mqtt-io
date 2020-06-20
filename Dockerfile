FROM python:3.6-alpine

ENV LANG C.UTF-8  
ENV LC_ALL C.UTF-8  

RUN apk add build-base
RUN pip install --no-cache-dir pipenv

WORKDIR /home/mqttgpio
RUN adduser --disabled-password --gecos "" --home "$(pwd)" --no-create-home -s /bin/bash mqttgpio
RUN addgroup -g 997 gpio
RUN addgroup mqttgpio gpio
RUN chown -R mqttgpio .
USER mqttgpio

COPY --chown=mqttgpio Pipfile ./
RUN pipenv install --three --deploy

COPY pi_mqtt_gpio pi_mqtt_gpio

CMD [ "pipenv", "run", "python", "-m", "pi_mqtt_gpio.server", "/config.yml" ]
