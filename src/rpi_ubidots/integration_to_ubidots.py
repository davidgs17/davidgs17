'''
Sends data to Ubidots using MQTT
Example provided by Jose Garcia @Ubidots Developer, modified a little bit by HAM
'''

import paho.mqtt.client as mqttClient
import time
import json
import random
import sys
import RPi.GPIO as GPIO
from hx711 import HX711
from gpiozero import Button

'''
global variables
'''
connected = False  # Stores the connection status
BROKER_ENDPOINT = "industrial.api.ubidots.com"
TLS_PORT = 1883  # MQTT port
MQTT_USERNAME = ""  # Put here your Ubidots TOKEN
MQTT_PASSWORD = ""  # Leave this in blank
TOPIC = "/v1.6/devices/"
DEVICE_LABEL = "" #Change this to your device label

# Button parameters
button1 = Button(4, bounce_time=1)
button2 = Button(14, bounce_time=1)

# Load Cell parameters
referenceUnit = 1
hx = HX711(5, 6)
hx.set_reading_format("MSB", "MSB")
hx.set_reference_unit(referenceUnit)
hx.reset()
hx.tare()
print("Tare done! Add weight now...")

'''
Functions to process incoming and outgoing streaming
'''

def on_connect(client, userdata, flags, rc):
    global connected  # Use global variable
    if rc == 0:

        print("[INFO] Connected to broker")
        connected = True  # Signal connection
    else:
        print("[INFO] Error, connection failed")


def on_publish(client, userdata, result):
    print("Published!")


def connect(mqtt_client, mqtt_username, mqtt_password, broker_endpoint, port):
    global connected

    if not connected:
        mqtt_client.username_pw_set(mqtt_username, password=mqtt_password)
        mqtt_client.on_connect = on_connect
        mqtt_client.on_publish = on_publish
        mqtt_client.connect(broker_endpoint, port=port)
        mqtt_client.loop_start()

        attempts = 0

        while not connected and attempts < 5:  # Wait for connection
            print(connected)
            print("Attempting to connect...")
            time.sleep(1)
            attempts += 1

    if not connected:
        print("[ERROR] Could not connect to broker")
        return False

    return True


def publish(mqtt_client, topic, payload):

    try:
        mqtt_client.publish(topic, payload)

    except Exception as e:
        print("[ERROR] Could not publish data, error: {}".format(e))


def main(mqtt_client):
    # read load cell value
    val = hx.get_weight(5)
    print(val)
    hx.power_down()
    hx.power_up()
    time.sleep(0.1)
    
    # read button status
    sort_status = 0 #0 for left open, 1 for right open
    if button1.is_pressed: 
        print("button 1 pressed")
        sort_status = 1
        time.sleep(1)
    elif button2.is_pressed: 
        print("button 2 pressed")
        sort_status = 0
        time.sleep(1)
    
    # publish the value to the ubidots
    payload = json.dumps({"item_weight": val, "sorting-status": sort_status})
    
    # publish two example
    # humidity = int(random.random()*100)
    # payload = json.dumps({"temperature": val, "humidity": humidity})
    
    topic = "{}{}".format(TOPIC, DEVICE_LABEL)
    if not connect(mqtt_client, MQTT_USERNAME,
                   MQTT_PASSWORD, BROKER_ENDPOINT, TLS_PORT):
        return False

    publish(mqtt_client, topic, payload)

    return True


if __name__ == '__main__':
    mqtt_client = mqttClient.Client()
    while True:
        main(mqtt_client)
        time.sleep(10)
