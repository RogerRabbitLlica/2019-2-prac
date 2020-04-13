#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function

import json
import logging
import signal
import sys
import threading
import time

import MqttClient
import Plotter

logger = logging.getLogger(__name__)

finished = False

plotter = None

mqtt_server = "85.214.232.187"

current_pwm  = 0.0
current_temp = 0.0
target_temp  = 0.0
delta_time   = 0.05

user_name = "usuario"
mqtt_topic_actuator = user_name + "/" + "actuator_control"
mqtt_topic_sensor   = user_name + "/" + "sensor_value"
mqtt_topic_pwm      = user_name + "/" + "actuator_pwm"

# Callback executed when user presses CTRL+C
def signal_handler(signal, frame):
    global finished
    logging.error("signal_handler")
    finished = True

# Callback executed when pid_controller publishes PWM value
def on_actuator_pwm(message):
    global plotter
    try:
        logging.info("on_actuator_pwm")
        current_pwm = json.loads(message)["pwm_value"]
        plotter.set_current_pwm(current_pwm)
    except:
        logging.error("on_actuator_pwm Exception")
        raise

# Callback executed when user sets a current_temp setpoint
def on_actuator_control(message):
    global plotter
    try:
        logging.info("on_actuator_control")
        target_temp = json.loads(message)["temperature"]
        plotter.set_target_temp(target_temp)
    except:
        logging.error("on_actuator_control Exception")
        raise


# Callback executed when digital_twin publishes current_temp value
def on_sensor_value(message):
    global plotter
    try:
        logging.info("on_actuator_control")
        current_temp = json.loads(message)["temperature"]
        plotter.set_current_temp(current_temp)
    except:
        logging.error("on_sensor_value Exception")
        raise

def main():
    global finished, plotter

    # Create logging file
    logging.basicConfig(filename='user_gui.log', filemode='w', level=logging.INFO)

    # Register interrupt handler
    signal.signal(signal.SIGINT, signal_handler)

    # Create asynchronous events
    plotEvent = threading.Event()

    plotter = Plotter.Plotter(event = plotEvent)
    plotter.start()

    # Create the MQTT client
    mqtt = MqttClient.MqttClient(address = mqtt_server)
    status = mqtt.setup()
    if (not status):
        logging.error("Error while connecting connecting to MQTT broker")
        exit()

    # Start the MQTT client
    mqtt.start()
    
    # Subsribe to on_actuator_control and on_sensor_value topics
    mqtt.add_topic(mqtt_topic_actuator, on_actuator_control)
    mqtt.add_topic(mqtt_topic_sensor, on_sensor_value)
    mqtt.add_topic(mqtt_topic_pwm, on_actuator_pwm)

    print("Press CTRL+C to stop!")

    # Run until finished
    while(not finished):
        try:           
            plotEvent.set()
        except:
            logging.error("main loop")

        # Wait until next execution
        time.sleep(delta_time)

    # Stop MQTT client
    mqtt.stop()

    plotter.exit()
    plotter.join()

if __name__ == "__main__":
    main()
