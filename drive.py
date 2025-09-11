from micromelon import *
import keyboard
import time

port = int(input("Please enter the code for your MicroMelon rover, usually displayed on the screen: "))
print("Trying to connect to rover", port)
rc = RoverController()
rc.connectBLE(port)
rc.startRover()

print("Welcome to Will's Script Hub! WASD to drive, Q to quit.")

running = True
while running:
    left, right = 0, 0

    if keyboard.is_pressed('w'):
        left, right = 30, 30
    if keyboard.is_pressed('s'):
        left, right = -30, -30
    if keyboard.is_pressed('a'):
        left, right = -30, 30
    if keyboard.is_pressed('d'):
        left, right = 30, -30
    if keyboard.is_pressed('q'):
        running = False

    Motors.write(left, right)
    time.sleep(0.05)

rc.stopRover()
rc.end()
