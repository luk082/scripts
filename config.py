"""
Configuration management for MicroMelon Rover Control System
Provides centralized settings with JSON serialization support.
"""

import json
import os
from dataclasses import dataclass, asdict
from typing import Dict, Tuple, Optional
from pathlib import Path


@dataclass
class RoverConfig:
    """Centralized configuration for all rover control systems"""
    
    # Connection settings
    default_ble_port: int = 1234
    simulator_address: str = "127.0.0.1"
    simulator_port: int = 9000
    connection_timeout: float = 10.0
    connection_retry_attempts: int = 3
    
    # Motor control settings
    max_motor_speed: int = 50
    min_motor_speed: int = -50
    turn_speed_differential: int = 20
    motor_acceleration_limit: float = 10.0  # units per second
    
    # Sensor settings
    sensor_update_interval: float = 0.5
    sensor_timeout: float = 2.0
    ultrasonic_max_range: float = 255.0
    battery_low_threshold: int = 20  # percent
    
    # Safety settings
    obstacle_distance_threshold: float = 20.0  # cm
    enable_collision_avoidance: bool = True
    emergency_stop_enabled: bool = True
    max_tilt_angle: float = 45.0  # degrees
    
    # Camera/Gesture settings
    camera_width: int = 640
    camera_height: int = 480
    camera_fps: int = 30
    gesture_confidence_threshold: float = 0.7
    prediction_history_length: int = 5
    gesture_model_path: str = "gesture_model.pkl"
    
    # UI settings
    window_width: int = 800
    window_height: int = 800
    fps_target: int = 60
    fullscreen_default: bool = False
    gui_theme: str = "dark"  # dark, light
    
    # Performance settings
    enable_performance_monitoring: bool = True
    log_performance_metrics: bool = False
    frame_skip_threshold: float = 0.1  # skip frames if processing takes longer
    
    # Logging settings
    log_level: str = "INFO"
    log_to_file: bool = True
    log_file_path: str = "rover.log"
    max_log_size: int = 10 * 1024 * 1024  # 10MB
    
    # Color scheme (11 standard colors)
    led_colors: Dict[str, Tuple[int, int, int]] = None
    
    def __post_init__(self):
        """Initialize default values that can't be set in dataclass"""
        if self.led_colors is None:
            self.led_colors = {
                "RED": (255, 0, 0),
                "GREEN": (0, 255, 0), 
                "BLUE": (0, 0, 255),
                "YELLOW": (255, 255, 0),
                "CYAN": (0, 255, 255),
                "MAGENTA": (255, 0, 255),
                "WHITE": (255, 255, 255),
                "ORANGE": (255, 165, 0),
                "PURPLE": (128, 0, 128),
                "LIME": (0, 255, 128),
                "PINK": (255, 192, 203)
            }
    
    @classmethod
    def load_from_file(cls, path: str = "rover_config.json") -> 'RoverConfig':
        """Load configuration from JSON file"""
        config_path = Path(path)
        
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Handle nested dictionaries properly
                config = cls()
                for key, value in data.items():
                    if hasattr(config, key):
                        setattr(config, key, value)
                
                print(f"Configuration loaded from {path}")
                return config
                
            except (json.JSONDecodeError, Exception) as e:
                print(f"Warning: Could not load config from {path}: {e}")
                print("Using default configuration")
                
        return cls()
    
    def save_to_file(self, path: str = "rover_config.json") -> bool:
        """Save configuration to JSON file"""
        try:
            config_dict = asdict(self)
            
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
            
            print(f"Configuration saved to {path}")
            return True
            
        except Exception as e:
            print(f"Error saving config to {path}: {e}")
            return False
    
    def update_from_dict(self, updates: Dict) -> None:
        """Update configuration from dictionary"""
        for key, value in updates.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                print(f"Warning: Unknown config key '{key}' ignored")
    
    def get_motor_limits(self) -> Tuple[int, int]:
        """Get motor speed limits as tuple (min, max)"""
        return (self.min_motor_speed, self.max_motor_speed)
    
    def get_camera_resolution(self) -> Tuple[int, int]:
        """Get camera resolution as tuple (width, height)"""
        return (self.camera_width, self.camera_height)
    
    def get_window_size(self) -> Tuple[int, int]:
        """Get window size as tuple (width, height)"""
        return (self.window_width, self.window_height)
    
    def is_gesture_confident(self, confidence: float) -> bool:
        """Check if gesture confidence meets threshold"""
        return confidence >= self.gesture_confidence_threshold
    
    def validate(self) -> Tuple[bool, list]:
        """Validate configuration values and return (is_valid, errors)"""
        errors = []
        
        # Validate motor speeds
        if self.max_motor_speed <= self.min_motor_speed:
            errors.append("max_motor_speed must be greater than min_motor_speed")
        
        if not (0 <= self.max_motor_speed <= 100):
            errors.append("max_motor_speed should be between 0 and 100")
        
        # Validate sensor settings
        if self.sensor_update_interval <= 0:
            errors.append("sensor_update_interval must be positive")
        
        # Validate camera settings
        if self.camera_width <= 0 or self.camera_height <= 0:
            errors.append("Camera dimensions must be positive")
        
        # Validate thresholds
        if not (0.0 <= self.gesture_confidence_threshold <= 1.0):
            errors.append("gesture_confidence_threshold must be between 0 and 1")
        
        if self.battery_low_threshold < 0 or self.battery_low_threshold > 100:
            errors.append("battery_low_threshold must be between 0 and 100")
        
        return len(errors) == 0, errors


def create_default_config_file():
    """Create default configuration file if it doesn't exist"""
    config_path = "rover_config.json"
    
    if not Path(config_path).exists():
        config = RoverConfig()
        config.save_to_file(config_path)
        print(f"Created default configuration file: {config_path}")
        return True
    return False


if __name__ == "__main__":
    # Demo/test the configuration system
    print("MicroMelon Rover Configuration System")
    print("=" * 40)
    
    # Create default config
    config = RoverConfig()
    
    # Show some settings
    print(f"Default motor limits: {config.get_motor_limits()}")
    print(f"Camera resolution: {config.get_camera_resolution()}")
    print(f"Gesture confidence threshold: {config.gesture_confidence_threshold}")
    
    # Validate configuration
    is_valid, errors = config.validate()
    print(f"\nConfiguration valid: {is_valid}")
    if errors:
        print("Errors found:")
        for error in errors:
            print(f"  - {error}")
    
    # Save and reload test
    print("\nTesting save/load...")
    config.save_to_file("test_config.json")
    loaded_config = RoverConfig.load_from_file("test_config.json")
    
    print(f"Original max speed: {config.max_motor_speed}")
    print(f"Loaded max speed: {loaded_config.max_motor_speed}")
    
    # Cleanup
    if Path("test_config.json").exists():
        Path("test_config.json").unlink()
        print("Cleanup complete")