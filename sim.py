from micromelon import *
import keyboard
import time

rc = RoverController()
rc.connectIP(address='127.0.0.1', port=9000)
rc.startRover()

print("Welcome to Will's Enhanced Script Hub!")
print("WASD to drive, Q to quit, SPACE to cycle LED colors")

color_list = [
    COLOURS.RED, COLOURS.GREEN, COLOURS.BLUE,
    COLOURS.YELLOW, COLOURS.CYAN, COLOURS.MAGENTA,
    COLOURS.WHITE, COLOURS.ORANGE, COLOURS.PURPLE,
    COLOURS.LIME, COLOURS.PINK
]

color_names = [
    "RED", "GREEN", "BLUE", "YELLOW", "CYAN",
    "MAGENTA", "WHITE", "ORANGE", "PURPLE", "LIME", "PINK"
]

current_color_index = 0
space_pressed = False

# initial LED colour (use .value to get the [r,g,b] array from the enum)
try:
    LEDs.writeAll(color_list[current_color_index].value)
    print(f"Initial LED color: {color_names[current_color_index]}")
except Exception as e:
    print(f"Error setting initial LED color: {e}")

running = True
while running:
    left, right = 0, 0

    # movement
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

    # cycle colours
    if keyboard.is_pressed('space'):
        if not space_pressed:
            space_pressed = True
            current_color_index = (current_color_index + 1) % len(color_list)
            try:
                LEDs.writeAll(color_list[current_color_index].value)
                print(f"LED color changed to: {color_names[current_color_index]}")
            except Exception as e:
                print(f"Error changing LED color: {e}")
    else:
        space_pressed = False

    Motors.write(left, right)
    time.sleep(0.05)

# Turn off LEDs when quitting
try:
    LEDs.off()
    print("LEDs turned off")
except Exception as e:
    print(f"Error turning off LEDs: {e}")

rc.stopRover()
rc.end()
