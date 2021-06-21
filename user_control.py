#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import logging
import signal
import sys
import threading
import time

import numpy as np

import MqttClient
import PIDController

logger = logging.getLogger(__name__)

finished = False
lock = threading.Lock()

mqtt_server = "35.205.249.237"

target_temp  = 0.0
delta_time   = 0.1
current_time = 0.0

user_name = "usuario"
mqtt_topic_actuator = user_name + "/" + "actuator_control"
mqtt_topic_sensor   = user_name + "/" + "sensor_value"

# Callback executed when user presses CTRL+C
def signal_handler(signal, frame):
    global finished
    logging.error("signal_handler")
    finished = True

# Callback executed when digital_twin publishes current_temp value
def on_sensor_value(message):
    global lock, current_temp
    if (lock.acquire(False)):
        try:
            current_temp = json.loads(message)["temperature"]
        except:
            logging.error("on_sensor_value Exception")
            raise
        finally:
            lock.release()

def main():
    global finished, lock
    global target_temp
    global delta_time, current_time

    # Create logging file
    logging.basicConfig(filename='user_control.log', filemode='w', level=logging.INFO)

    # Register interrupt handler
    signal.signal(signal.SIGINT, signal_handler)

    # Create the MQTT client
    mqtt = MqttClient.MqttClient(address = mqtt_server)
    status = mqtt.setup()
    if (not status):
        logging.error("Error while connecting connecting to MQTT broker")
        exit()

    # Start the MQTT client
    mqtt.start()

    # Subsribe to on_sensor_value topic
    mqtt.add_topic(mqtt_topic_sensor, on_sensor_value)

    # Run until finished
    while(not finished):
        target_temp = 50.0 + 25*np.sign(np.sin(2*np.pi*current_time/100))
        
        # Create MQTT message with current PWM value
        mqtt_message = json.dumps({"temperature": target_temp}, sort_keys=True)

        # Send MQTT message with current PWM value
        mqtt.send_message(mqtt_topic_actuator, mqtt_message)

        # Acquire lock non-blocking
        if (lock.acquire(False)):
            try:
                error_temp = current_temp - target_temp

                print("target_temp={:.2f}".format(target_temp))
                print("current_temp={:.2f}".format(current_temp))
                print("error_temp={:.2f}".format(error_temp))
                print("*****")
            except:
                logging.error("main loop")
            finally:
                lock.release()

        # Wait until next execution
        time.sleep(delta_time)
        current_time += delta_time

    # Stop MQTT client
    mqtt.stop()

if __name__ == "__main__":
    main()
