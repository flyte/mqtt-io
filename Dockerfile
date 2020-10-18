from python:3.6-stretch

ENV LANG C.UTF-8  
ENV LC_ALL C.UTF-8  

RUN pip install --no-cache-dir pipenv

RUN useradd -m -s /bin/bash mqttgpio
USER mqttgpio
WORKDIR /home/mqttgpio

COPY Pipfile* ./
RUN pipenv install --three --deploy

COPY pi_mqtt_gpio pi_mqtt_gpio

CMD [ "pipenv", "run", "python", "-m", "pi_mqtt_gpio.server", "/config.yml" ]
