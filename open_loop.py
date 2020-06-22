#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import logging
import signal
import sys
import threading
import time

from threading import Thread

import MqttClient
import PIDController

logger = logging.getLogger(__name__)

finished = False
lock = threading.Lock()

current_pwm = 0
delta_time  = 0.1

mqtt_server = "35.233.1.50"

user_name = "usuario"
mqtt_topic_pwm = user_name + "/" + "actuator_pwm"

# Callback executed when user presses CTRL+C
def signal_handler(signal, frame):
    global finished
    logging.error("signal_handler")
    finished = True

def get_user_intput():
    global finished, lock, current_pwm

    # Run until finished
    while(not finished):
        try:
            user_input = int(raw_input('Introduce el valor de PWM (0-100%): '))
            if (user_input >= 0 and user_input <= 100):
                if (lock.acquire(True)):
                    current_pwm = user_input
                    lock.release()
            else:
                print("Valor de PWM introducido incorrecto!")
        except:
            logging.error("get_user_input Exception")
            finished = True

def main():
    global finished, lock, current_pwm

    # Create logging file
    logging.basicConfig(filename='open_loop.log', filemode='w', level=logging.INFO)

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

    # Create user input thread
    thread = Thread(target = get_user_intput)
    thread.start()

    # Run until finished
    while(not finished):
        # Acquire lock non-blocking
        if (lock.acquire(False)):
            try:
                # Create MQTT message with current PWM value
                mqtt_message = json.dumps({"pwm_value": current_pwm})

                # Send MQTT message with current PWM value
                mqtt.send_message(mqtt_topic_pwm, mqtt_message)
            except:
                logging.error("main loop")
            finally:
                lock.release()

        # Wait until next execution
        time.sleep(delta_time)
        
    # Stop MQTT client
    mqtt.stop()

    # Wait for thread to finish
    thread.join()

if __name__ == "__main__":
    main()
