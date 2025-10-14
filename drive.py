from micromelon import *
import keyboard
import time
import sys
connected = False
rc = RoverController()
while connected == False:
    portinput = input("input port: ")
    if not portinput.isdigit() or len(portinput) != 4:
        print("failed, try again with a four digit integer")
        continue
    port = int(portinput)
    print(f'attempting to perform handshake on port {port}')
    try:
        rc.connectBLE(port)
        connected = True
    except TimeoutError:
        print("failed, connection timeout")
    except Exception as e:
        print("unexpected error:", e)
        sys.exit(1)
Robot.setName("bambussy")
rc.startRover()
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
try:
    LEDs.writeAll(color_list[current_color_index].value)
except Exception as e:
    print(f"error setting initial led color: {e}")
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
    if keyboard.is_pressed('u'):
        ultrasonic = Ultrasonic.read()
        if ultrasonic == 255:
            print("ultrasonic unavailable")
        else:
            print("ultrasonic:", ultrasonic)
    if keyboard.is_pressed('b'):
        current = Battery.readCurrent()
        percentage = Battery.readPercentage()
        voltage = Battery.readVoltage()
        print(str(current) + "mA", str(percentage) + "%", str(voltage) + "V")
        time.sleep(0.2)
    if keyboard.is_pressed('x'):
        accelx = IMU.readAccel(n=0)
        gyrox = IMU.readGyro(n=0)
        gyroax = IMU.readGyroAccum(n=0)
        print(f'accelx: {accelx}, gyrox: {gyrox}, gyroaccumx: {gyroax}')
        time.sleep(0.2)
    if keyboard.is_pressed('y'):
        accely = IMU.readAccel(n=1)
        gyroy = IMU.readGyro(n=1)
        gyroay = IMU.readGyroAccum(n=1)
        print(f'accely: {accely}, gyroy: {gyroy}, gyroaccumy: {gyroay}')
        time.sleep(0.2)
    if keyboard.is_pressed('z'):
        accelz = IMU.readAccel(n=2)
        gyroz = IMU.readGyro(n=2)
        gyroaz = IMU.readGyroAccum(n=2)
        print(f'accelz: {accelz}, gyroz: {gyroz}, gyroaccumz: {gyroaz}')
        time.sleep(0.2)
    if keyboard.is_pressed('f'):
        flipped = IMU.isFlipped()
        if flipped == True:
            print('flipped state')
        elif flipped == False:
            print('righted state')
    if keyboard.is_pressed('l'):
        leftir = IR.readLeft()
        print(f'leftir: {leftir}')
    if keyboard.is_pressed('r'):
        rightir = IR.readRight()
        print(f'rightir: {rightir}')
    if keyboard.is_pressed('n'):
        newname = input("input new name: ")
        Robot.setname(newname)
    if keyboard.is_pressed('c'):
        if not space_pressed:
            space_pressed = True
            current_color_index = (current_color_index + 1) % len(color_list)
            try:
                LEDs.writeAll(color_list[current_color_index].value)
            except Exception as e:
                print(f"error changing led color: {e}")
    else:
        space_pressed = False
    Motors.write(left, right)
    time.sleep(0.05)
try:
    LEDs.off()
except Exception as e:
    print(f"error turning off leds: {e}")

rc.stopRover()
rc.end()