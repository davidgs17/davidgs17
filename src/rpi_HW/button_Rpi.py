# Here is the configuration:
# Connect your button NO pin to GPIO 4 & 14 (pin 7 & 8)
# Connect your button COM pin to GND

from gpiozero import Button
import time

button1 = Button(4, bounce_time=1)
button2 = Button(14, bounce_time=1)

while True: 
    if button1.is_pressed: 
        print("button 1 pressed")
        time.sleep(1)
    elif button2.is_pressed: 
        print("button 2 pressed")
        time.sleep(1)
