"""
Graphical user interface for MicroMelon Rover Control System
Control the rover using a modern GUI interface.

This interface closely follows the structure of guidrive.py
"""

import pygame
import time
import sys

class GUIInterface:
    """Graphical user interface for rover control"""
    
    def __init__(self, rover, config):
        self.rover = rover  # This is the rover object created by create_rover_controller
        self.config = config
        
        # Initialize pygame
        pygame.init()
        
        # Constants
        self.WINDOW_WIDTH = 900
        self.WINDOW_HEIGHT = 600
        self.BG_COLOR = (0, 0, 0)
        self.GREEN = (0, 255, 0)
        self.DARK_GREEN = (0, 100, 0)
        self.FONT = pygame.font.Font(pygame.font.match_font('courier'), 14)
        self.TITLE_FONT = pygame.font.Font(pygame.font.match_font('courier'), 18)
        
        # Setup pygame window
        self.screen = pygame.display.set_mode((self.WINDOW_WIDTH, self.WINDOW_HEIGHT))
        pygame.display.set_caption("MicroMelon Rover Controller")
        self.clock = pygame.time.Clock()
        
        # Color definitions (RGB for display)
        self.color_rgb = [
            (255, 0, 0), (0, 255, 0), (0, 0, 255),
            (255, 255, 0), (0, 255, 255), (255, 0, 255),
            (255, 255, 255), (255, 165, 0), (128, 0, 128),
            (0, 255, 0), (255, 192, 203)
        ]
        self.color_names = [
            "RED", "GREEN", "BLUE", "YELLOW", "CYAN",
            "MAGENTA", "WHITE", "ORANGE", "PURPLE", "LIME", "PINK"
        ]
        self.current_color_index = 0
        
        # Create UI elements
        self.create_buttons()
        
        # Sensor data
        self.sensor_data = {
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
        
        self.last_sensor_update = 0
        self.sensor_update_interval = 0.5  # 2Hz
        
        # Control state
        self.running = True
        
        print("GUI interface initialized")
    
    def enable_session_recording(self, session_name):
        """Enable session recording (placeholder)"""
        print(f"Session recording enabled: {session_name}")
    
    def create_buttons(self):
        """Create UI buttons"""
        # Key button class
        class KeyButton:
            def __init__(self, x, y, width, height, label):
                self.rect = pygame.Rect(x, y, width, height)
                self.label = label
                self.active = False
            
            def draw(self, surface, green, dark_green, font):
                color = green if self.active else dark_green
                pygame.draw.rect(surface, color, self.rect, 2)
                if self.active:
                    pygame.draw.rect(surface, dark_green, self.rect)
                    pygame.draw.rect(surface, green, self.rect, 3)
                text = font.render(self.label, True, green)
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
            
            def draw(self, surface, is_selected, green, dark_green, font):
                pygame.draw.rect(surface, self.color, self.rect)
                pygame.draw.rect(surface, green if is_selected else dark_green, self.rect, 2)
                text = font.render(self.name, True, green)
                text_rect = text.get_rect(center=(self.rect.centerx, self.rect.bottom + 15))
                surface.blit(text, text_rect)
            
            def is_clicked(self, pos):
                return self.rect.collidepoint(pos)
        
        # Create WASD buttons
        key_size = 60
        key_spacing = 70
        base_x = 50
        base_y = 80
        
        self.w_button = KeyButton(base_x + key_spacing, base_y, key_size, key_size, "W")
        self.a_button = KeyButton(base_x, base_y + key_spacing, key_size, key_size, "A")
        self.s_button = KeyButton(base_x + key_spacing, base_y + key_spacing, key_size, key_size, "S")
        self.d_button = KeyButton(base_x + key_spacing * 2, base_y + key_spacing, key_size, key_size, "D")
        
        self.key_buttons = {
            'w': self.w_button,
            'a': self.a_button,
            's': self.s_button,
            'd': self.d_button
        }
        
        # Create color buttons
        self.color_buttons = []
        colors_per_row = 6
        color_button_size = 35
        color_start_x = 50
        color_start_y = 380
        
        for i, (color, name) in enumerate(zip(self.color_rgb, self.color_names)):
            row = i // colors_per_row
            col = i % colors_per_row
            x = color_start_x + col * (color_button_size + 20)
            y = color_start_y + row * (color_button_size + 35)
            self.color_buttons.append(ColorButton(x, y, color_button_size, color_button_size, color, name, i))
        
        # Quit button
        self.quit_button = pygame.Rect(self.WINDOW_WIDTH - 120, self.WINDOW_HEIGHT - 60, 100, 40)
        
        # Store button positions for reference
        self.base_x = base_x
        self.base_y = base_y
        self.color_start_x = color_start_x
        self.color_start_y = color_start_y
    
    def update_sensors(self):
        """Update sensor readings from rover"""
        try:
            # Get sensor data from rover
            sensors = self.rover.get_sensors()
            
            # Update sensor data dictionary
            if hasattr(sensors, 'ultrasonic') and sensors.ultrasonic is not None:
                self.sensor_data['ultrasonic'] = str(sensors.ultrasonic) if sensors.ultrasonic != 255 else 'N/A'
            else:
                self.sensor_data['ultrasonic'] = 'N/A'
            
            # Battery data
            if hasattr(sensors, 'battery_current') and sensors.battery_current is not None:
                self.sensor_data['battery_current'] = f"{sensors.battery_current}mA"
            else:
                self.sensor_data['battery_current'] = 'N/A'
            
            if hasattr(sensors, 'battery_percentage') and sensors.battery_percentage is not None:
                self.sensor_data['battery_percentage'] = f"{sensors.battery_percentage}%"
            else:
                self.sensor_data['battery_percentage'] = 'N/A'
            
            if hasattr(sensors, 'battery_voltage') and sensors.battery_voltage is not None:
                self.sensor_data['battery_voltage'] = f"{sensors.battery_voltage}V"
            else:
                self.sensor_data['battery_voltage'] = 'N/A'
            
            # IMU data
            if hasattr(sensors, 'accel_x') and sensors.accel_x is not None:
                self.sensor_data['accel_x'] = str(sensors.accel_x)
                self.sensor_data['accel_y'] = str(sensors.accel_y) if sensors.accel_y is not None else 'N/A'
                self.sensor_data['accel_z'] = str(sensors.accel_z) if sensors.accel_z is not None else 'N/A'
            else:
                self.sensor_data['accel_x'] = 'N/A'
                self.sensor_data['accel_y'] = 'N/A'
                self.sensor_data['accel_z'] = 'N/A'
            
            if hasattr(sensors, 'gyro_x') and sensors.gyro_x is not None:
                self.sensor_data['gyro_x'] = str(sensors.gyro_x)
                self.sensor_data['gyro_y'] = str(sensors.gyro_y) if sensors.gyro_y is not None else 'N/A'
                self.sensor_data['gyro_z'] = str(sensors.gyro_z) if sensors.gyro_z is not None else 'N/A'
            else:
                self.sensor_data['gyro_x'] = 'N/A'
                self.sensor_data['gyro_y'] = 'N/A'
                self.sensor_data['gyro_z'] = 'N/A'
            
            # Simplified for now - rover system may not have all these sensors
            self.sensor_data['gyro_accum_x'] = 'N/A'
            self.sensor_data['gyro_accum_y'] = 'N/A'  
            self.sensor_data['gyro_accum_z'] = 'N/A'
            
            if hasattr(sensors, 'is_flipped') and sensors.is_flipped is not None:
                self.sensor_data['flipped'] = 'Yes' if sensors.is_flipped else 'No'
            else:
                self.sensor_data['flipped'] = 'N/A'
            
            if hasattr(sensors, 'ir_left') and sensors.ir_left is not None:
                self.sensor_data['ir_left'] = str(sensors.ir_left)
            else:
                self.sensor_data['ir_left'] = 'N/A'
            
            if hasattr(sensors, 'ir_right') and sensors.ir_right is not None:
                self.sensor_data['ir_right'] = str(sensors.ir_right)
            else:
                self.sensor_data['ir_right'] = 'N/A'
                
        except Exception as e:
            print(f"Sensor update error: {e}")
            # Set all sensors to error state
            for key in self.sensor_data:
                self.sensor_data[key] = 'Error'
    
    def run(self):
        """Main interface loop"""
        print("\\n" + "="*60)
        print("MicroMelon Rover GUI Control")
        print("="*60)
        print("Controls:")
        print("  - Use WASD keys or click buttons to control rover")
        print("  - Click color buttons to change LED colors")
        print("  - Press 'q' or click QUIT to exit")
        print("="*60 + "\\n")
        
        try:
            while self.running:
                current_time = time.time()
                
                # Update sensors at 2Hz
                if current_time - self.last_sensor_update >= self.sensor_update_interval:
                    self.update_sensors()
                    self.last_sensor_update = current_time
                
                # Handle pygame events
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        pos = pygame.mouse.get_pos()
                        
                        # Check WASD buttons
                        for key, button in self.key_buttons.items():
                            if button.is_clicked(pos):
                                button.active = True
                        
                        # Check color buttons
                        for color_button in self.color_buttons:
                            if color_button.is_clicked(pos):
                                self.current_color_index = color_button.index
                                try:
                                    if hasattr(self.rover, 'cycle_led_color'):
                                        # Use rover's built-in LED cycling
                                        color = self.rover.cycle_led_color()
                                        print(f"LED color changed to: {color}")
                                    else:
                                        print(f"LED color selected: {self.color_names[self.current_color_index]}")
                                except Exception as e:
                                    print(f"LED control error: {e}")
                        
                        # Check quit button
                        if self.quit_button.collidepoint(pos):
                            self.running = False
                    
                    elif event.type == pygame.MOUSEBUTTONUP:
                        # Deactivate clicked buttons
                        for button in self.key_buttons.values():
                            button.active = False
                
                # Handle keyboard input
                keys = pygame.key.get_pressed()
                left, right = 0, 0
                
                if keys[pygame.K_w]:
                    self.w_button.active = True
                    left, right = 30, 30
                else:
                    self.w_button.active = False
                
                if keys[pygame.K_s]:
                    self.s_button.active = True
                    left, right = -30, -30
                else:
                    self.s_button.active = False
                
                if keys[pygame.K_a]:
                    self.a_button.active = True
                    left, right = -30, 30
                else:
                    self.a_button.active = False
                
                if keys[pygame.K_d]:
                    self.d_button.active = True
                    left, right = 30, -30
                else:
                    self.d_button.active = False
                
                if keys[pygame.K_q]:
                    self.running = False
                
                # Apply motor control
                try:
                    self.rover.set_motor_speeds(left, right)
                except Exception as e:
                    print(f"Motor control error: {e}")
                
                # Drawing
                self.draw_interface(left, right)
                
                pygame.display.flip()
                self.clock.tick(60)  # 60 FPS
                time.sleep(0.05)
        
        except KeyboardInterrupt:
            print("\\nKeyboard interrupt")
        finally:
            print("\\nShutting down...")
            self.cleanup()
    
    def draw_interface(self, left_motor, right_motor):
        """Draw the complete interface"""
        self.screen.fill(self.BG_COLOR)
        
        # Draw title
        title = self.TITLE_FONT.render("MICROMELON ROVER CONTROLLER", True, self.GREEN)
        self.screen.blit(title, (20, 20))
        
        # Draw WASD control section
        control_title = self.FONT.render("CONTROLS", True, self.GREEN)
        self.screen.blit(control_title, (self.base_x, self.base_y - 30))
        
        for button in self.key_buttons.values():
            button.draw(self.screen, self.GREEN, self.DARK_GREEN, self.FONT)
        
        # Draw sensor section - split into two columns
        sensor_x = 300
        sensor_y = 80
        sensor_title = self.FONT.render("SENSORS", True, self.GREEN)
        self.screen.blit(sensor_title, (sensor_x, sensor_y - 30))
        
        # Left column sensors
        left_sensors = [
            f"Ultrasonic: {self.sensor_data['ultrasonic']}",
            f"Battery: {self.sensor_data['battery_percentage']}",
            f"Voltage: {self.sensor_data['battery_voltage']}",
            f"Current: {self.sensor_data['battery_current']}",
            f"Accel X: {self.sensor_data['accel_x']}",
            f"Accel Y: {self.sensor_data['accel_y']}",
            f"Accel Z: {self.sensor_data['accel_z']}"
        ]
        
        # Right column sensors
        right_sensors = [
            f"Gyro X: {self.sensor_data['gyro_x']}",
            f"Gyro Y: {self.sensor_data['gyro_y']}",
            f"Gyro Z: {self.sensor_data['gyro_z']}",
            f"IR Left: {self.sensor_data['ir_left']}",
            f"IR Right: {self.sensor_data['ir_right']}",
            f"Flipped: {self.sensor_data['flipped']}",
            ""
        ]
        
        # Draw left column
        for i, label in enumerate(left_sensors):
            text = self.FONT.render(label, True, self.GREEN)
            self.screen.blit(text, (sensor_x, sensor_y + i * 20))
        
        # Draw right column
        for i, label in enumerate(right_sensors):
            if label:  # Skip empty strings
                text = self.FONT.render(label, True, self.GREEN)
                self.screen.blit(text, (sensor_x + 250, sensor_y + i * 20))
        
        # Draw color picker section
        color_title = self.FONT.render("LED COLORS", True, self.GREEN)
        self.screen.blit(color_title, (self.color_start_x, self.color_start_y - 30))
        
        for color_button in self.color_buttons:
            color_button.draw(self.screen, color_button.index == self.current_color_index, 
                            self.GREEN, self.DARK_GREEN, self.FONT)
        
        # Draw quit button
        pygame.draw.rect(self.screen, self.DARK_GREEN, self.quit_button)
        pygame.draw.rect(self.screen, self.GREEN, self.quit_button, 2)
        quit_text = self.FONT.render("QUIT", True, self.GREEN)
        quit_text_rect = quit_text.get_rect(center=self.quit_button.center)
        self.screen.blit(quit_text, quit_text_rect)
        
        # Draw motor status
        motor_text = self.FONT.render(f"Motors: L={left_motor} R={right_motor}", True, self.GREEN)
        self.screen.blit(motor_text, (50, self.WINDOW_HEIGHT - 40))
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            self.rover.set_motor_speeds(0, 0)
            print("Motors stopped")
        except Exception as e:
            print(f"Error during cleanup: {e}")
        
        pygame.quit()
        print("Shutdown complete")


if __name__ == "__main__":
    print("Direct testing not supported - use through rover.py")