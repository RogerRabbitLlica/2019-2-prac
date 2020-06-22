#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import logging
import math
import signal
import sys
import threading
import time

import numpy as np

import MqttClient

logger = logging.getLogger(__name__)

finished = False
lock = threading.Lock()

mqtt_server = "35.233.1.50"

old_pwm      = 0.0
current_pwm  = 0.0

old_temp     = 24.0
current_temp = 24.0
old_time     = 0.0
current_time = 0.0
delta_time   = 0.1

user_name = "usuario"
mqtt_topic_pwm    = user_name + "/" + "actuator_pwm"
mqtt_topic_sensor = user_name + "/" + "sensor_value"

# Callback executed when user presses CTRL+C
def signal_handler(signal, frame):
    global finished
    logging.error("signal_handler")
    finished = True

# Callback executed when pid_controller publishes PWM value
def on_actuator_pwm(message):
    global lock, current_pwm
    # if (lock.acquire(True)):
    if (lock.acquire(False)):
        try:
            current_pwm = json.loads(message)["pwm_value"]
        except:
            logging.error("on_actuator_pwm Exception")
            raise
        finally:
            lock.release()

def roundup(x):
    value = int(math.ceil(x / 10.0)) * 10
    if (value > 100):
        value = 100
    if (value < 0):
        value = 0
    return value

def calculate_temperature(T_inicial, T_actual, pwm_inicial, pwm_actual, t_inicial, t_actual, T_max, tau):
    tambient = 24.0
    tmax = 120.0
    temperature = 0.0

    # If the PWM is above or below previous, we
    # need to update the T_inicial and T_max variables
    if (pwm_actual != pwm_inicial):
        T_inicial = T_actual
        T_max = T_max - T_actual
        pwm_inicial = pwm_actual
        t_inicial = t_actual


    if (T_max != T_inicial):
        # Time elapsed since we last changed PWM
        dt = t_actual - t_inicial
 
        # New temperature value
        temperature = T_max * (1 - np.exp(-dt/tau)) + T_inicial
    else:
        tempererature = T_inicial

    # Ensure temperature does not go above sensor limits
    if (temperature > tmax):
        temperature = tmax
    
    # Ensure temperature does not go below ambient
    if (temperature < tambient):
        temperature = tambient

    return (temperature, T_inicial, pwm_inicial, t_inicial, T_max)

# Exponential increase for each PWM
values = {  "0": [24.000, 1.0/0.0140],
           "10": [31.563, 1.0/0.0125],
           "20": [46.206, 1.0/0.0126],
           "30": [55.828, 1.0/0.0136],
           "40": [70.865, 1.0/0.0136],
           "50": [80.067, 1.0/0.0146],
           "60": [87.043, 1.0/0.0149],
           "70": [93.824, 1.0/0.0142],
           "80": [95.276, 1.0/0.0155],
           "90": [95.912, 1.0/0.0153],
          "100": [96.137, 1.0/0.0143]}

def main():
    global finished, lock
    global current_pwm, current_temp, current_time
    global old_pwm, old_temp, old_time
    global delta_time

    # Create logging file
    logging.basicConfig(filename='digital_twin.log', filemode='w', level=logging.INFO)

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

    # Subsribe to on_actuator_pwm topic
    mqtt.add_topic(mqtt_topic_pwm, on_actuator_pwm)
    
    t_max = 0.0
    tau   = 0.0
    init_pwm = False

    # Run until finished
    while(not finished):
        # Acquire lock non-blocking
        if (lock.acquire(False)):
            try:
                 # Obtain t_max and tau coefficients for the current PWM
                if (current_pwm != old_pwm or init_pwm == False):
                    t_max, tau = values[str(roundup(int(current_pwm)))]
                    init_pwm = True

                # Calculate current_temp baed on delta_time and current_pwm
                current_temp, old_temp, old_pwm, old_time, t_max = calculate_temperature(old_temp, current_temp, old_pwm, current_pwm, old_time, current_time, t_max, tau)

                # Create MQTT message with current temperature
                mqtt_message = json.dumps({"temperature": current_temp})
                
                # Send MQTT message with current temperature
                mqtt.send_message(mqtt_topic_sensor, mqtt_message)

                print("current_temp={:.2f}".format(current_temp))
                print("current_pwm={:.2f}".format(current_pwm))
                print("current_time={}".format(current_time))
                print("*****")
            except:
                logging.error("main Exception")
                raise
            finally:
                lock.release()

        # Increase simulation time
        current_time += delta_time

        # Wait until next execution
        time.sleep(delta_time)

    # Stop MQTT client
    mqtt.stop()

if __name__ == "__main__":   
    main()
