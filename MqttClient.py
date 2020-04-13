# -*- coding: utf-8 -*-

import json
import logging
import threading
import time

import paho.mqtt.client as mqtt

from collections import OrderedDict

class MqttClient(object):
    def __init__(self, address = "127.0.0.1", port = 1883):
        logging.info("__init__")

        # Lock to wait for connection
        self.lock = threading.Lock()
        self.lock.acquire()

        # Store the MQTT server, port and timeout
        self.mqtt_address = address
        self.mqtt_port    = port
        self.mqtt_timeout = 30

        self.mqtt_client = None
        self.mqtt_subscriptions = {}

    def mqtt_on_connect(self, client, data, flags, rc):
        logging.info("connected")
        # Release lock to signal connection
        self.lock.release()

    def mqtt_on_message(self, client, userdata, msg):
        #logging.info("message received")
        topic = msg.topic
        payload = msg.payload.decode('utf-8')

        self.mqtt_subscriptions[topic](payload)

    def setup(self):
        logging.info("setup")

        # Create MQTT client
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self.mqtt_on_connect
        self.mqtt_client.on_message = self.mqtt_on_message

        return True

    def start(self):
        logging.info("start")

        # Connect the MQTT client to the broker
        self.mqtt_client.connect(self.mqtt_address, self.mqtt_port, self.mqtt_timeout)

        # Start the MQTT client
        self.mqtt_client.loop_start()

        # Wait for connection
        self.lock.acquire()

    def stop(self):
        logging.info("stop")

        # Stop the MQTT thread
        self.mqtt_client.loop_stop()

    def add_topic(self, topic, callback):
        logging.info("subscribed to topic={}".format(topic))

        self.mqtt_client.subscribe(topic)

        self.mqtt_subscriptions[topic] = callback

    def send_message(self, mqtt_topic, mqtt_message):
        # Log the message that has been send
        logging.info("send message: {}".format(mqtt_message))

        # Publish the JSON message to the MQTT broker
        self.mqtt_client.publish(mqtt_topic, mqtt_message)
    