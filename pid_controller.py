#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import logging
import signal
import sys
import threading
import time

import MqttClient
import PIDController

logger = logging.getLogger(__name__)

finished = False
lock = threading.Lock()

mqtt_server = "35.233.1.50"

pid_kp = 100.0
pid_ki = 20.0
pid_kd = 1.0

current_pwm  = 0.0
current_temp = 0.0
target_temp  = 0.0
delta_time   = 0.1

user_name = "usuario"
mqtt_topic_actuator = user_name + "/" + "actuator_control"
mqtt_topic_sensor   = user_name + "/" + "sensor_value"
mqtt_topic_pwm      = user_name + "/" + "actuator_pwm"

# Callback executed when user presses CTRL+C
def signal_handler(signal, frame):
    global finished
    logging.error("signal_handler")
    finished = True

# Callback executed when user sets a current_temp setpoint
def on_actuator_control(message):
    global lock, target_temp
    if (lock.acquire(False)):
        try:
            target_temp = json.loads(message)["temperature"]
        except:
            logging.error("on_actuator_control Exception")
            raise
        finally:
            lock.release()

# Callback executed when digital_twin publishes current_temp value
def on_sensor_value(message):
    global lock, current_temp
    if (lock.acquire(False)):
        try:
            current_temp = json.loads(message)["temperature"]
        except:
            logging.error("on_sensor_value")
            raise
        finally:
            lock.release()

def main():
    global finished, lock
    global current_pwm, target_temp, current_temp
    global pid_kp, pid_ki, pid_kd

    # Create logging file
    logging.basicConfig(filename='pid_controller.log', filemode='w', level=logging.INFO)

    # Register interrupt handler
    signal.signal(signal.SIGINT, signal_handler)

    # Create PID controller and configure it
    pid = PIDController.PIDController(pid_kp, pid_ki, pid_kd)
    pid.setSampleTime(delta_time)
    pid.setSetPoint(target_temp)
    pid.setWindup(1.0)

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

    # Run until finished
    while(not finished):
        # Acquire lock non-blocking
        if (lock.acquire(False)):
            try:
                # Set the new target temperature
                pid.setSetPoint(target_temp)

                # Update the PID based on the current temperature
                pid.update(current_temp)

                # Get the updated PWM value
                current_pwm = pid.getOutput()

                # Create MQTT message with current PWM value
                mqtt_message = json.dumps({"pwm_value": current_pwm})

                # Send MQTT message with current PWM value
                mqtt.send_message(mqtt_topic_pwm, mqtt_message)
                
                print("target_temp={:.2f}".format(target_temp))
                print("current_temp={:.2f}".format(current_temp))
                print("current_pwm={:.2f}".format(current_pwm))
                print("*****")
            except:
                logging.error("main loop")
            finally:
                lock.release()

        # Wait until next execution
        time.sleep(delta_time)

    # Stop MQTT client
    mqtt.stop()

if __name__ == "__main__":
    main()
