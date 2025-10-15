"""
Modern keyboard interface for MicroMelon Rover Control System
Enhanced version of the original drive.py with professional features.
"""

import time
import sys
from typing import Dict, Optional
import keyboard

from config import RoverConfig
from rover_base import RoverControllerBase, SensorData
from error_handling import setup_global_logging, PerformanceMonitor


class KeyboardInterface:
    """Modern keyboard interface with enhanced features"""
    
    def __init__(self, rover: RoverControllerBase, config: RoverConfig):
        self.rover = rover
        self.config = config
        self.logger = setup_global_logging(config).get_logger("KeyboardInterface")
        self.performance_monitor = PerformanceMonitor(config)
        
        # Control state
        self.running = True
        self.motor_speeds = {"left": 0, "right": 0}
        self.current_sensors = SensorData()
        
        # Display settings
        self.show_sensors = True
        self.show_help = True
        self.last_sensor_display = 0.0
        self.sensor_display_interval = 1.0  # Update sensor display every second
        
        # Session recording
        self.session_recording = False
        self.session_recorder = None
        
        self.logger.info("Keyboard interface initialized")
    
    def enable_session_recording(self, session_name: str):
        """Enable session recording with given name"""
        # This would be implemented with a session recorder class
        self.session_recording = True
        self.logger.info(f"Session recording enabled: {session_name}")
    
    def display_welcome(self):
        """Display welcome message and controls"""
        print("\n" + "=" * 70)
        print("🚀 MicroMelon Rover - Enhanced Keyboard Control")
        print("=" * 70)
        print(f"Connected to: {'Physical Rover' if isinstance(self.rover, type(self.rover)) else 'Simulator'}")
        print(f"Safety systems: {'Enabled' if self.config.enable_collision_avoidance else 'Disabled'}")
        print("=" * 70)
        
        if self.show_help:
            self.display_help()
    
    def display_help(self):
        """Display control help"""
        print("\n📋 CONTROLS:")
        print("  Movement:")
        print("    W/S - Forward/Backward    A/D - Turn Left/Right")
        print("  ")
        print("  Sensors:")
        print("    U - Read ultrasonic       B - Battery info")
        print("    X/Y/Z - IMU accel/gyro    F - Check if flipped")
        print("    L/R - Left/Right IR       I - All sensor info")
        print("  ")
        print("  System:")
        print("    C - Cycle LED colors      N - Change rover name")
        print("    H - Toggle help display   S - Toggle sensor display")
        print("    ESC/Q - Quit              SPACE - Emergency stop")
        print("=" * 70)
    
    def display_status(self):
        """Display current rover status"""
        current_time = time.time()
        
        # Update sensors periodically
        if current_time - self.last_sensor_display >= self.sensor_display_interval:
            self.current_sensors = self.rover.get_sensors()
            self.last_sensor_display = current_time
            
            if self.show_sensors:
                self.clear_sensor_area()
                self.print_sensor_info()
        
        # Always show current motor speeds and LED color
        self.print_status_line()
    
    def clear_sensor_area(self):
        """Clear the sensor display area"""
        # Move cursor up and clear lines (basic implementation)
        pass
    
    def print_sensor_info(self):
        """Print sensor information"""
        sensors = self.current_sensors
        
        print(f"\n📊 SENSORS ({time.strftime('%H:%M:%S')}):")
        print(f"  Ultrasonic: {sensors.ultrasonic if sensors.ultrasonic else 'N/A'} cm")
        
        if sensors.battery_percentage is not None:
            battery_status = "🔋" if sensors.battery_percentage > 50 else "🪫" if sensors.battery_percentage > 20 else "⚠️"
            print(f"  Battery: {battery_status} {sensors.battery_percentage}% ({sensors.battery_voltage}V, {sensors.battery_current}mA)")
        
        if sensors.is_flipped is not None:
            flip_status = "⚠️ FLIPPED" if sensors.is_flipped else "✓ Upright"
            print(f"  Orientation: {flip_status}")
        
        if sensors.ir_left is not None and sensors.ir_right is not None:
            print(f"  IR Sensors: Left={sensors.ir_left}, Right={sensors.ir_right}")
    
    def print_status_line(self):
        """Print current status line"""
        status = self.rover.get_status()
        
        # Motor speeds with direction indicators
        left_arrow = "←" if self.motor_speeds["left"] < 0 else "→" if self.motor_speeds["left"] > 0 else "○"
        right_arrow = "←" if self.motor_speeds["right"] < 0 else "→" if self.motor_speeds["right"] > 0 else "○"
        
        motor_display = f"Motors: {left_arrow} L={self.motor_speeds['left']:3d} | R={self.motor_speeds['right']:3d} {right_arrow}"
        
        # LED color with indicator
        led_display = f"LED: 💡 {status['current_led_color']}"
        
        # Safety status
        safety_status = status['safety']
        safety_display = "🛡️" if safety_status['collision_avoidance_enabled'] else "⚠️"
        if safety_status['emergency_stop_active']:
            safety_display = "🛑 EMERGENCY STOP"
        
        print(f"\r{motor_display} | {led_display} | {safety_display}", end="", flush=True)
    
    def handle_movement_keys(self):
        """Handle movement key inputs"""
        left_speed = 0
        right_speed = 0
        
        # Get motor speed from config
        max_speed = self.config.max_motor_speed
        turn_speed = self.config.turn_speed_differential
        
        # Check movement keys
        if keyboard.is_pressed('w'):
            left_speed = max_speed
            right_speed = max_speed
        elif keyboard.is_pressed('s'):
            left_speed = -max_speed // 2  # Slower reverse
            right_speed = -max_speed // 2
        
        if keyboard.is_pressed('a'):  # Turn left
            left_speed -= turn_speed
            right_speed += turn_speed
        elif keyboard.is_pressed('d'):  # Turn right
            left_speed += turn_speed
            right_speed -= turn_speed
        
        # Update motor speeds if changed
        if self.motor_speeds["left"] != left_speed or self.motor_speeds["right"] != right_speed:
            self.motor_speeds["left"] = left_speed
            self.motor_speeds["right"] = right_speed
            success = self.rover.set_motor_speeds(left_speed, right_speed)
            
            if not success:
                self.logger.warning("Motor command blocked by safety system")
    
    def handle_sensor_keys(self):
        """Handle sensor reading key inputs"""
        if keyboard.is_pressed('u'):
            sensors = self.rover.get_sensors()
            if sensors.ultrasonic is not None:
                print(f"\n🔊 Ultrasonic: {sensors.ultrasonic} cm")
            else:
                print("\n⚠️ Ultrasonic sensor unavailable")
            time.sleep(0.2)
        
        elif keyboard.is_pressed('b'):
            sensors = self.rover.get_sensors()
            if sensors.battery_percentage is not None:
                print(f"\n🔋 Battery: {sensors.battery_percentage}% ({sensors.battery_voltage}V, {sensors.battery_current}mA)")
            else:
                print("\n⚠️ Battery info unavailable")
            time.sleep(0.2)
        
        elif keyboard.is_pressed('f'):
            sensors = self.rover.get_sensors()
            if sensors.is_flipped is not None:
                status = "⚠️ FLIPPED!" if sensors.is_flipped else "✓ Upright"
                print(f"\n🔄 Orientation: {status}")
            else:
                print("\n⚠️ Orientation sensor unavailable")
            time.sleep(0.2)
        
        elif keyboard.is_pressed('i'):
            # Display all sensor info immediately
            self.current_sensors = self.rover.get_sensors()
            self.print_sensor_info()
            time.sleep(0.5)
        
        elif keyboard.is_pressed('x'):
            sensors = self.rover.get_sensors()
            if sensors.accel_x is not None:
                print(f"\n📊 Accel X: {sensors.accel_x:.3f}, Gyro X: {sensors.gyro_x:.3f}")
            time.sleep(0.2)
        
        elif keyboard.is_pressed('y'):
            sensors = self.rover.get_sensors()
            if sensors.accel_y is not None:
                print(f"\n📊 Accel Y: {sensors.accel_y:.3f}, Gyro Y: {sensors.gyro_y:.3f}")
            time.sleep(0.2)
        
        elif keyboard.is_pressed('z'):
            sensors = self.rover.get_sensors()
            if sensors.accel_z is not None:
                print(f"\n📊 Accel Z: {sensors.accel_z:.3f}, Gyro Z: {sensors.gyro_z:.3f}")
            time.sleep(0.2)
        
        elif keyboard.is_pressed('l'):
            sensors = self.rover.get_sensors()
            if sensors.ir_left is not None:
                print(f"\n👈 IR Left: {sensors.ir_left}")
            time.sleep(0.2)
        
        elif keyboard.is_pressed('r'):
            sensors = self.rover.get_sensors()
            if sensors.ir_right is not None:
                print(f"\n👉 IR Right: {sensors.ir_right}")
            time.sleep(0.2)
    
    def handle_system_keys(self):
        """Handle system control key inputs"""
        if keyboard.is_pressed('c'):
            color = self.rover.cycle_led_color()
            print(f"\n💡 LED color: {color}")
            time.sleep(0.3)  # Prevent rapid cycling
        
        elif keyboard.is_pressed('n'):
            try:
                new_name = input("\n🏷️ Enter new rover name: ").strip()
                if new_name:
                    # This would set the rover name if supported
                    print(f"Rover name set to: {new_name}")
                else:
                    print("Name change cancelled")
            except KeyboardInterrupt:
                print("Name change cancelled")
            time.sleep(0.2)
        
        elif keyboard.is_pressed('h'):
            self.show_help = not self.show_help
            if self.show_help:
                self.display_help()
            else:
                print("\n📋 Help hidden (press H to show)")
            time.sleep(0.3)
        
        elif keyboard.is_pressed('s'):
            self.show_sensors = not self.show_sensors
            status = "shown" if self.show_sensors else "hidden"
            print(f"\n📊 Sensor display {status}")
            time.sleep(0.3)
        
        elif keyboard.is_pressed('space'):
            # Emergency stop
            self.rover.safety_manager.trigger_emergency_stop("Manual emergency stop")
            self.rover.set_motor_speeds(0, 0, apply_safety=False)
            self.motor_speeds = {"left": 0, "right": 0}
            print(f"\n🛑 EMERGENCY STOP ACTIVATED!")
            print("Press R to reset emergency stop")
            time.sleep(0.5)
        
        elif keyboard.is_pressed('esc') or keyboard.is_pressed('q'):
            print(f"\n👋 Shutting down...")
            self.running = False
    
    def handle_emergency_reset(self):
        """Handle emergency stop reset"""
        if keyboard.is_pressed('r'):
            if self.rover.safety_manager.emergency_stop_active:
                self.rover.safety_manager.reset_emergency_stop()
                print(f"\n✓ Emergency stop reset")
                time.sleep(0.3)
    
    def run(self):
        """Main interface loop"""
        try:
            self.display_welcome()
            
            # Main control loop
            while self.running:
                frame_start = self.performance_monitor.start_frame()
                
                # Handle all input types
                self.handle_movement_keys()
                self.handle_sensor_keys() 
                self.handle_system_keys()
                self.handle_emergency_reset()
                
                # Update display
                self.display_status()
                
                # Performance monitoring
                self.performance_monitor.end_frame(frame_start)
                
                # Small sleep to prevent excessive CPU usage
                time.sleep(0.05)  # 20 FPS max
                
        except KeyboardInterrupt:
            print(f"\n⚠️ Interrupted by user")
        except Exception as e:
            self.logger.error(f"Interface error: {e}")
            print(f"\n❌ Error: {e}")
        finally:
            # Ensure motors are stopped
            try:
                self.rover.set_motor_speeds(0, 0, apply_safety=False)
                print(f"\n🔧 Motors stopped")
            except:
                pass
            
            self.logger.info("Keyboard interface shutdown")
            print("🏁 Interface closed\n")


if __name__ == "__main__":
    # Direct run for testing
    print("Testing keyboard interface with simulator...")
    
    from config import RoverConfig
    from rover_base import create_rover_controller
    
    config = RoverConfig()
    
    try:
        with create_rover_controller(config, 'simulator') as rover:
            interface = KeyboardInterface(rover, config)
            interface.run()
    except Exception as e:
        print(f"Test failed: {e}")