from micromelon import *
import pygame
import time
import sys

# Initialize pygame
pygame.init()

# Constants
WINDOW_SIZE = 500
BG_COLOR = (0, 0, 0)
GREEN = (0, 255, 0)
DARK_GREEN = (0, 100, 0)
FONT = pygame.font.Font(pygame.font.match_font('jetbrainsmono'), 16)
TITLE_FONT = pygame.font.Font(pygame.font.match_font('jetbrainsmono'), 20)

# Connect to rover simulator
rc = RoverController()
print("connecting to simulator at 127.0.0.1:9000")
try:
    rc.connectIP(address="127.0.0.1", port=9000)
    print("debug: connected to simulator")
except Exception as e:
    print("debug: connection error:", e)
    sys.exit(1)

Robot.setName("bambussy")
rc.startRover()

# Color definitions
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
color_rgb = [
    (255, 0, 0), (0, 255, 0), (0, 0, 255),
    (255, 255, 0), (0, 255, 255), (255, 0, 255),
    (255, 255, 255), (255, 165, 0), (128, 0, 128),
    (0, 255, 0), (255, 192, 203)
]
current_color_index = 0

try:
    LEDs.writeAll(color_list[current_color_index].value)
except Exception as e:
    print(f"debug: error setting initial led color: {e}")

# Setup pygame window
screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
pygame.display.set_caption("Rover Controller (Simulator)")
clock = pygame.time.Clock()

# Key button class
class KeyButton:
    def __init__(self, x, y, width, height, label):
        self.rect = pygame.Rect(x, y, width, height)
        self.label = label
        self.active = False
    
    def draw(self, surface):
        color = GREEN if self.active else DARK_GREEN
        pygame.draw.rect(surface, color, self.rect, 2)
        if self.active:
            pygame.draw.rect(surface, DARK_GREEN, self.rect)
            pygame.draw.rect(surface, GREEN, self.rect, 3)
        text = FONT.render(self.label, True, GREEN)
        text_rect = text.get_rect(center=self.rect.center)
        surface.blit(text, text_rect)
    
    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

# Color picker button class
class ColorButton:
    def __init__(self, x, y, width, height, color, name, index):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        self.name = name
        self.index = index
    
    def draw(self, surface, is_selected):
        pygame.draw.rect(surface, self.color, self.rect)
        pygame.draw.rect(surface, GREEN if is_selected else DARK_GREEN, self.rect, 2)
    
    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

# Create WASD buttons
key_size = 50
key_spacing = 70
base_x = 20
base_y = 100

w_button = KeyButton(base_x + key_spacing, base_y, key_size, key_size, "W")
a_button = KeyButton(base_x, base_y + key_spacing, key_size, key_size, "A")
s_button = KeyButton(base_x + key_spacing, base_y + key_spacing, key_size, key_size, "S")
d_button = KeyButton(base_x + key_spacing * 2, base_y + key_spacing, key_size, key_size, "D")

key_buttons = {
    'w': w_button,
    'a': a_button,
    's': s_button,
    'd': d_button
}

# Create color buttons
color_buttons = []
colors_per_row = 4
color_button_size = 30
color_start_x = 20
color_start_y = 300

for i, (color, name) in enumerate(zip(color_rgb, color_names)):
    row = i // colors_per_row
    col = i % colors_per_row
    x = color_start_x + col * (color_button_size + 20)
    y = color_start_y + row * (color_button_size + 20)
    color_buttons.append(ColorButton(x, y, color_button_size, color_button_size, color, name, i))

# Quit button
quit_button = pygame.Rect(WINDOW_SIZE - 120, WINDOW_SIZE - 60, 100, 40)

# Sensor data
sensor_data = {
    'ultrasonic': 'N/A',
    'battery_current': 'N/A',
    'battery_percentage': 'N/A',
    'battery_voltage': 'N/A',
    'accel_x': 'N/A',
    'accel_y': 'N/A',
    'accel_z': 'N/A',
    'gyro_x': 'N/A',
    'gyro_y': 'N/A',
    'gyro_z': 'N/A',
    'gyro_accum_x': 'N/A',
    'gyro_accum_y': 'N/A',
    'gyro_accum_z': 'N/A',
    'flipped': 'N/A',
    'ir_left': 'N/A',
    'ir_right': 'N/A'
}

last_sensor_update = 0
sensor_update_interval = 0.005  # 200Hz

def update_sensors():
    try:
        ultrasonic = Ultrasonic.read()
        sensor_data['ultrasonic'] = str(ultrasonic) if ultrasonic != 255 else 'N/A'
    except:
        sensor_data['ultrasonic'] = 'Error'
    
    try:
        sensor_data['battery_current'] = f"{Battery.readCurrent()}mA"
        sensor_data['battery_percentage'] = f"{Battery.readPercentage()}%"
        sensor_data['battery_voltage'] = f"{Battery.readVoltage()}V"
    except:
        sensor_data['battery_current'] = 'Error'
        sensor_data['battery_percentage'] = 'Error'
        sensor_data['battery_voltage'] = 'Error'
    
    try:
        sensor_data['accel_x'] = str(IMU.readAccel(n=0))
        sensor_data['gyro_x'] = str(IMU.readGyro(n=0))
        sensor_data['gyro_accum_x'] = str(IMU.readGyroAccum(n=0))
    except:
        sensor_data['accel_x'] = 'Error'
        sensor_data['gyro_x'] = 'Error'
        sensor_data['gyro_accum_x'] = 'Error'
    
    try:
        sensor_data['accel_y'] = str(IMU.readAccel(n=1))
        sensor_data['gyro_y'] = str(IMU.readGyro(n=1))
        sensor_data['gyro_accum_y'] = str(IMU.readGyroAccum(n=1))
    except:
        sensor_data['accel_y'] = 'Error'
        sensor_data['gyro_y'] = 'Error'
        sensor_data['gyro_accum_y'] = 'Error'
    
    try:
        sensor_data['accel_z'] = str(IMU.readAccel(n=2))
        sensor_data['gyro_z'] = str(IMU.readGyro(n=2))
        sensor_data['gyro_accum_z'] = str(IMU.readGyroAccum(n=2))
    except:
        sensor_data['accel_z'] = 'Error'
        sensor_data['gyro_z'] = 'Error'
        sensor_data['gyro_accum_z'] = 'Error'
    
    try:
        flipped = IMU.isFlipped()
        sensor_data['flipped'] = 'Yes' if flipped else 'No'
    except:
        sensor_data['flipped'] = 'Error'
    
    try:
        sensor_data['ir_left'] = str(IR.readLeft())
        sensor_data['ir_right'] = str(IR.readRight())
    except:
        sensor_data['ir_left'] = 'Error'
        sensor_data['ir_right'] = 'Error'

# Main loop
running = True
while running:
    current_time = time.time()
    
    # Update sensors at 2Hz
    if current_time - last_sensor_update >= sensor_update_interval:
        update_sensors()
        last_sensor_update = current_time
    
    # Handle pygame events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()
            
            # Check WASD buttons
            for key, button in key_buttons.items():
                if button.is_clicked(pos):
                    button.active = True
            
            # Check color buttons
            for color_button in color_buttons:
                if color_button.is_clicked(pos):
                    current_color_index = color_button.index
                    try:
                        LEDs.writeAll(color_list[current_color_index].value)
                        print(f"debug: led color changed to {color_names[current_color_index]}")
                    except Exception as e:
                        print(f"debug: error changing led color: {e}")
            
            # Check quit button
            if quit_button.collidepoint(pos):
                running = False
        
        elif event.type == pygame.MOUSEBUTTONUP:
            # Deactivate clicked buttons
            for button in key_buttons.values():
                button.active = False
    
    # Handle keyboard input
    keys = pygame.key.get_pressed()
    left, right = 0, 0
    
    if keys[pygame.K_w]:
        w_button.active = True
        left, right = 30, 30
    else:
        w_button.active = False
    
    if keys[pygame.K_s]:
        s_button.active = True
        left, right = -30, -30
    else:
        s_button.active = False
    
    if keys[pygame.K_a]:
        a_button.active = True
        left, right = -30, 30
    else:
        a_button.active = False
    
    if keys[pygame.K_d]:
        d_button.active = True
        left, right = 30, -30
    else:
        d_button.active = False
    
    if keys[pygame.K_q]:
        running = False
    
    # Apply motor control
    Motors.write(left, right)
    
    # Drawing
    screen.fill(BG_COLOR)
    
    # Draw title
    title = TITLE_FONT.render("simulator controller", True, GREEN)
    screen.blit(title, (20, 20))
    
    # Draw WASD control section
    control_title = FONT.render("controls", True, GREEN)
    screen.blit(control_title, (20, 50))
    
    for button in key_buttons.values():
        button.draw(screen)
    
    # Draw sensor section
    sensor_x = 245
    sensor_y = 80
    sensor_title = FONT.render("sensors", True, GREEN)
    screen.blit(sensor_title, (sensor_x, 50))
    
    sensor_labels = [
        f"ultrasonic: {sensor_data['ultrasonic']}",
        f"battery: {sensor_data['battery_current']} {sensor_data['battery_percentage']} {sensor_data['battery_voltage']}",
        f"accel x: {sensor_data['accel_x']}",
        f"accel y: {sensor_data['accel_y']}",
        f"accel z: {sensor_data['accel_z']}",
        f"gyro x: {sensor_data['gyro_x']}",
        f"gyro y: {sensor_data['gyro_y']}",
        f"gyro z: {sensor_data['gyro_z']}",
        f"gyro accum x: {sensor_data['gyro_accum_x']}",
        f"gyro accum y: {sensor_data['gyro_accum_y']}",
        f"gyro accum z: {sensor_data['gyro_accum_z']}",
        f"flipped: {sensor_data['flipped']}",
        f"ir left: {sensor_data['ir_left']}",
        f"ir right: {sensor_data['ir_right']}"
    ]
    
    for i, label in enumerate(sensor_labels):
        text = FONT.render(label, True, GREEN)
        screen.blit(text, (sensor_x, sensor_y + i * 22))
    
    # Draw color picker section
    color_title = FONT.render("colours", True, GREEN)
    screen.blit(color_title, (20, color_start_y - 30))
    
    for color_button in color_buttons:
        color_button.draw(screen, color_button.index == current_color_index)
    
    # Draw quit button
    pygame.draw.rect(screen, DARK_GREEN, quit_button)
    pygame.draw.rect(screen, GREEN, quit_button, 2)
    quit_text = FONT.render("quit", True, GREEN)
    quit_text_rect = quit_text.get_rect(center=quit_button.center)
    screen.blit(quit_text, quit_text_rect)
    
    pygame.display.flip()
    clock.tick(60)  # 60 FPS
    time.sleep(0.05)

# Cleanup
print("debug: shutting down")
try:
    LEDs.off()
except Exception as e:
    print(f"debug: error turning off leds: {e}")

rc.stopRover()
rc.end()
pygame.quit()