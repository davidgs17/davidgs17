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
import pigpio

'''
global variables
'''
connected = False  # Stores the connection status
BROKER_ENDPOINT = "industrial.api.ubidots.com"
TLS_PORT = 1883  # MQTT port
MQTT_USERNAME = "BBFF-zhhCEt5jTqSQQNVcnWBK6GjrjiQJal"  # Put here your Ubidots TOKEN
MQTT_PASSWORD = ""  # Leave this in blank
TOPIC = "/v1.6/devices/"
DEVICE_LABEL = "188_eligible" #Change this to your device label 

# Button parameters
button1 = Button(21, bounce_time=1)
button2 = Button(22, bounce_time=1)

# Load Cell parameters
referenceUnit = -1089  
hx = HX711(5, 6)
hx.set_reading_format("MSB", "MSB")
hx.set_reference_unit(referenceUnit)
hx.reset()
hx.tare()
print("Tare done! Add weight now...")

#Servo parameter
servo = 18
pwm = pigpio.pi()
pwm.set_mode(servo, pigpio.OUTPUT)
pwm.set_PWM_frequency( servo, 50 )
#pwm.set_PWM_dutycycle( servo,0)

#sorting initial state
sort_status = 0 #0 for left open, 1 for right open
sort_command = 0 #0 for idle, 1 for sorting
dut_cyc = 0

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
    #print("Published!")
    pass


def connect(mqtt_client, mqtt_username, mqtt_password, broker_endpoint, port):
    global connected

    if not connected:
        mqtt_client.username_pw_set(mqtt_username, password=mqtt_password)
        mqtt_client.on_connect = on_connect
        mqtt_client.on_publish = on_publish
        mqtt_client.connect(broker_endpoint, port=port)
        SUB_LABEL = "188_eligible/#"
        topic = "{}{}".format(TOPIC, SUB_LABEL)
        mqtt_client.subscribe(topic)
        mqtt_client.on_message = on_message
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

def on_message(client, userdata, message):
    global sort_command
    if message.topic == "/v1.6/devices/188_eligible/command_sortir/lv":
        print("incoming data: " ,str(message.payload.decode("utf-8")))
        command = str(message.payload.decode("utf-8"))
        if command == "1.0":
            sort_command = 1
        else:
            sort_command = 0

def main(mqtt_client):
    global sort_status, sort_command, dut_cyc
    # read load cell value
    val = round(hx.get_weight(5),1) #change this value to 1 decimal rounding float
    #val = int(hx.get_weight(5)) #try integer
    #print(val, type(val))
    hx.power_down()
    hx.power_up()
    time.sleep(0.1)
    
    # read button status
    # button 1, servo right open, button 2 left open
    if button1.is_pressed: 
        print("button 1 pressed")
        sort_status = 1
        time.sleep(1)
    elif button2.is_pressed: 
        print("button 2 pressed")
        sort_status = 0
        time.sleep(1)
    
    # publish the value to the ubidots
    payload = json.dumps({"item_weight": val, "sort_data": sort_status})
    
    if sort_command: #sorting command received
        if val > 450 and not sort_status: # move servo to open right
            sort_move = True
            print("move to open right!")
            while sort_move:
                pwm.set_PWM_dutycycle(servo,10)
                if button1.is_pressed: 
                    print("open right reached!")
                    pwm.set_PWM_dutycycle(servo,0)
                    sort_status = 1
                    sort_command = 0
                    payload = json.dumps({"item_weight": val, "sort_data": sort_status,\
                                  "command_sortir": sort_command})
                    time.sleep(1)
                    sort_move = False
        elif val < 450 and sort_status:   # move servo to open left
            sort_move = True
            print("move to open left!")
            while sort_move:
                pwm.set_PWM_dutycycle(servo,30)
                if button2.is_pressed: 
                    print("open left reached!")
                    pwm.set_PWM_dutycycle(servo,0)
                    sort_status = 0
                    sort_command = 0
                    payload = json.dumps({"item_weight": val, "sort_data": sort_status,\
                                  "command_sortir": sort_command})
                    time.sleep(1)
                    sort_move = False
        else:
            sort_command = 0
            payload = json.dumps({"item_weight": val, "sort_data": sort_status,\
                                  "command_sortir": sort_command})
    
    print("item weight: "+str(val)+" sort_data: "+str(sort_status)+\
          " sort_command: "+str(sort_command))
        
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
        time.sleep(1)