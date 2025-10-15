"""
Hand gesture interface for MicroMelon Rover Control System
Control the rover using hand gestures detected via camera.

This interface closely follows the structure of gesturedrive.py
"""

import cv2
import numpy as np
import pickle
import mediapipe as mp
import time
import sys
from collections import Counter

class GestureInterface:
    """Hand gesture interface for rover control"""
    
    def __init__(self, rover, config):
        self.rover = rover  # This is the rover object created by create_rover_controller
        self.config = config
        
        # Performance configuration
        self.CAMERA_WIDTH = getattr(config, 'camera_width', 640)
        self.CAMERA_HEIGHT = getattr(config, 'camera_height', 480) 
        self.PROCESS_EVERY_N_FRAMES = 1
        self.MP_MODEL_COMPLEXITY = 1
        self.DRAW_LANDMARKS = False
        
        # UI Configuration
        self.WINDOW_NAME = "MicroMelon Gesture Control"
        self.FULLSCREEN_MODE = False  # Start in windowed mode to avoid overflow
        
        # Initialize MediaPipe with fastest settings
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            model_complexity=self.MP_MODEL_COMPLEXITY,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.mp_draw = mp.solutions.drawing_utils
        
        # Load gesture model
        self.load_model()
        
        # Initialize camera
        self.init_camera()
        
        # Control state
        self.running = True
        self.current_gesture = "none"
        self.gesture_confidence = 0.0
        self.control_active = False
        
        # Sensor data
        self.sensor_data = {
            'ultrasonic': 'n/a',
            'battery_percentage': 'n/a', 
            'battery_voltage': 'n/a',
            'ir_left': 'n/a',
            'ir_right': 'n/a'
        }
        
        self.last_sensor_update = 0
        self.sensor_update_interval = 2.0
        
        # Prediction smoothing
        self.prediction_history = []
        self.history_length = 2
        
        # Gesture mapping
        self.GESTURE_MAP = {
            'x+': (30, 30),   # forward
            'x-': (-20, -20), # backward  
            'y+': (5, 10),    # slight right
            'y-': (10, 5),    # slight left
            'n': (0, 0)       # stop
        }
        
        # FPS tracking
        self.fps_start_time = time.time()
        self.fps_frame_count = 0
        self.current_fps = 0
        
        print("Gesture interface initialized")
    
    def enable_session_recording(self, session_name):
        """Enable session recording (placeholder)"""
        print(f"Session recording enabled: {session_name}")
    
    def load_model(self):
        """Load gesture recognition model"""
        print("Loading gesture model...")
        try:
            model_path = getattr(self.config, 'gesture_model_path', 'gesture_model.pkl')
            with open(model_path, 'rb') as f:
                model_data = pickle.load(f)
                self.model = model_data['model']
                self.gesture_names = model_data['gesture_names']
            print(f"Model loaded with gestures: {self.gesture_names}")
        except Exception as e:
            print(f"Error loading model: {e}")
            print("Using fallback gesture detection")
            self.model = None
            self.gesture_names = ['x+', 'x-', 'y+', 'y-', 'n']
    
    def init_camera(self):
        """Initialize camera"""
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("Webcam error")
            sys.exit(1)
        
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.CAMERA_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.CAMERA_HEIGHT)
        self.cap.set(cv2.CAP_PROP_FPS, 60)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        print(f"Camera initialized: {self.CAMERA_WIDTH}x{self.CAMERA_HEIGHT}")
    
    def extract_landmarks(self, hand_landmarks):
        """Extract hand landmarks for gesture recognition"""
        FINGER_TIPS = np.array([4, 8, 12, 16, 20])
        
        landmarks = np.array([[lm.x, lm.y, lm.z] for lm in hand_landmarks.landmark])
        
        wrist = landmarks[0]
        normalized = landmarks - wrist
        normalized = normalized.flatten()
        
        palm_size = np.linalg.norm(landmarks[0] - landmarks[9])
        if palm_size > 0:
            normalized = normalized / palm_size
        
        # Add finger tip distances
        for tip_idx in FINGER_TIPS:
            distance = np.linalg.norm(landmarks[tip_idx] - wrist)
            if palm_size > 0:
                normalized = np.append(normalized, distance / palm_size)
            else:
                normalized = np.append(normalized, distance)
        
        return normalized
    
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
            
            if hasattr(sensors, 'battery_percentage') and sensors.battery_percentage is not None:
                self.sensor_data['battery_percentage'] = f"{sensors.battery_percentage}%"
            else:
                self.sensor_data['battery_percentage'] = 'N/A'
            
            if hasattr(sensors, 'battery_voltage') and sensors.battery_voltage is not None:
                self.sensor_data['battery_voltage'] = f"{sensors.battery_voltage}V"
            else:
                self.sensor_data['battery_voltage'] = 'N/A'
            
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
    
    def gesture_to_motor_command(self, gesture):
        """Convert gesture to motor commands"""
        return self.GESTURE_MAP.get(gesture, (0, 0))
    
    def run(self):
        """Main interface loop"""
        # Create window
        cv2.namedWindow(self.WINDOW_NAME, cv2.WINDOW_NORMAL)
        if self.FULLSCREEN_MODE:
            cv2.setWindowProperty(self.WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        else:
            # Set a reasonable window size
            cv2.resizeWindow(self.WINDOW_NAME, 800, 600)
        
        print("\\n" + "="*60)
        print("MicroMelon Gesture Control FAST MODE")
        print("="*60)
        print("Controls:")
        print("  - Use hand gestures to control the rover")
        print("  - Press 'c' to cycle LED colors (if available)")
        print("  - Press 'd' to toggle landmark drawing")
        print("  - Press 'f' to toggle fullscreen")
        print("  - Press 'q' or 'esc' to quit")
        print("="*60 + "\\n")
        
        try:
            while self.running:
                current_time = time.time()
                
                # Update sensors infrequently
                if current_time - self.last_sensor_update >= self.sensor_update_interval:
                    self.update_sensors()
                    self.last_sensor_update = current_time
                
                # Capture frame
                ret, frame = self.cap.read()
                if not ret:
                    print("Error reading frame")
                    break
                
                # Flip horizontally
                frame = cv2.flip(frame, 1)
                
                # Convert to RGB once
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Process hand detection
                results = self.hands.process(rgb_frame)
                
                if results.multi_hand_landmarks:
                    self.control_active = True
                    hand_landmarks = results.multi_hand_landmarks[0]
                    
                    # Draw landmarks if enabled
                    if self.DRAW_LANDMARKS:
                        self.mp_draw.draw_landmarks(
                            frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS,
                            self.mp_draw.DrawingSpec(color=(0, 255, 0), thickness=1, circle_radius=2),
                            self.mp_draw.DrawingSpec(color=(255, 255, 255), thickness=1)
                        )
                    
                    # Extract and predict
                    if self.model:
                        landmarks = self.extract_landmarks(hand_landmarks)
                        landmarks_array = landmarks.reshape(1, -1)
                        
                        prediction = self.model.predict(landmarks_array)[0]
                        proba = self.model.predict_proba(landmarks_array)
                        confidence = np.max(proba)
                        
                        # Minimal smoothing
                        self.prediction_history.append(prediction)
                        if len(self.prediction_history) > self.history_length:
                            self.prediction_history.pop(0)
                        
                        # Quick majority vote
                        if len(self.prediction_history) >= 2:
                            smoothed_prediction = Counter(self.prediction_history).most_common(1)[0][0]
                            prediction = smoothed_prediction
                        
                        self.current_gesture = prediction
                        self.gesture_confidence = confidence
                    else:
                        # Simple fallback gesture detection
                        h, w, _ = frame.shape
                        cx = int(hand_landmarks.landmark[9].x * w)
                        cy = int(hand_landmarks.landmark[9].y * h)
                        
                        center_x, center_y = w // 2, h // 2
                        
                        if cy < center_y - 50:
                            self.current_gesture = "x+"
                        elif cy > center_y + 50:
                            self.current_gesture = "x-"
                        elif cx < center_x - 50:
                            self.current_gesture = "y-"
                        elif cx > center_x + 50:
                            self.current_gesture = "y+"
                        else:
                            self.current_gesture = "n"
                        
                        self.gesture_confidence = 0.8
                else:
                    self.control_active = False
                    self.current_gesture = "no hand"
                    self.gesture_confidence = 0.0
                    self.prediction_history.clear()
                
                # Apply motor control
                left_motor, right_motor = self.gesture_to_motor_command(self.current_gesture)
                try:
                    self.rover.set_motor_speeds(left_motor, right_motor)
                except Exception as e:
                    print(f"Motor control error: {e}")
                
                # Calculate FPS
                self.fps_frame_count += 1
                if current_time - self.fps_start_time >= 1.0:
                    self.current_fps = self.fps_frame_count / (current_time - self.fps_start_time)
                    self.fps_frame_count = 0
                    self.fps_start_time = current_time
                
                # Draw UI
                self.draw_ui(frame, left_motor, right_motor)
                
                # Show frame
                cv2.imshow(self.WINDOW_NAME, frame)
                
                # Handle keyboard
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('q') or key == 27:
                    self.running = False
                elif key == ord('d'):
                    self.DRAW_LANDMARKS = not self.DRAW_LANDMARKS
                    print(f"Landmark drawing: {'ON' if self.DRAW_LANDMARKS else 'OFF'}")
                elif key == ord('f'):
                    self.FULLSCREEN_MODE = not self.FULLSCREEN_MODE
                    if self.FULLSCREEN_MODE:
                        cv2.setWindowProperty(self.WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
                    else:
                        cv2.setWindowProperty(self.WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)
                elif key == ord('c'):
                    # Cycle LED color if available
                    try:
                        if hasattr(self.rover, 'cycle_led_color'):
                            color = self.rover.cycle_led_color()
                            print(f"LED color changed to: {color}")
                    except Exception as e:
                        print(f"LED control error: {e}")
                
        except KeyboardInterrupt:
            print("\\nKeyboard interrupt")
        finally:
            print("\\nShutting down...")
            self.cleanup()
    
    def draw_ui(self, frame, left_motor, right_motor):
        """Draw UI elements on frame"""
        # Get frame dimensions
        h, w = frame.shape[:2]
        
        # Use smaller font sizes and better spacing
        title_font_scale = 0.6
        main_font_scale = 0.5
        small_font_scale = 0.4
        font_thickness = 1
        
        y = 25
        line_height = 20
        
        # Title with FPS (smaller)
        cv2.putText(frame, f"Gesture Control - {self.current_fps:.1f} FPS", 
                   (10, y), cv2.FONT_HERSHEY_SIMPLEX, title_font_scale, (0, 255, 255), font_thickness)
        y += line_height + 5
        
        # Gesture status
        gesture_color = (0, 255, 0) if self.control_active else (0, 0, 255)
        cv2.putText(frame, f"Gesture: {self.current_gesture.upper()}", 
                   (10, y), cv2.FONT_HERSHEY_SIMPLEX, main_font_scale, gesture_color, font_thickness)
        y += line_height
        
        # Confidence bar (smaller)
        if self.gesture_confidence > 0:
            bar_width = 150
            bar_height = 12
            cv2.rectangle(frame, (10, y), (10 + bar_width, y + bar_height), (50, 50, 50), -1)
            
            confidence_filled = int(self.gesture_confidence * bar_width)
            bar_color = (0, 255, 0) if self.gesture_confidence > 0.7 else (0, 165, 255)
            cv2.rectangle(frame, (10, y), (10 + confidence_filled, y + bar_height), bar_color, -1)
            cv2.rectangle(frame, (10, y), (10 + bar_width, y + bar_height), (255, 255, 255), 1)
            
            cv2.putText(frame, f"{self.gesture_confidence*100:.0f}%", 
                       (170, y + 10), cv2.FONT_HERSHEY_SIMPLEX, small_font_scale, (255, 255, 255), font_thickness)
            y += line_height + 5
        
        # Motors
        cv2.putText(frame, f"Motors: L={left_motor} R={right_motor}", 
                   (10, y), cv2.FONT_HERSHEY_SIMPLEX, main_font_scale, (255, 255, 255), font_thickness)
        y += line_height + 5
        
        # Sensors (compact, two columns if needed)
        cv2.putText(frame, "Sensors:", (10, y), cv2.FONT_HERSHEY_SIMPLEX, main_font_scale, (255, 255, 255), font_thickness)
        y += line_height - 2
        
        # Left column sensors
        cv2.putText(frame, f"Dist: {self.sensor_data['ultrasonic']}", 
                   (10, y), cv2.FONT_HERSHEY_SIMPLEX, small_font_scale, (255, 255, 255), font_thickness)
        y += 15
        
        cv2.putText(frame, f"Batt: {self.sensor_data['battery_percentage']}", 
                   (10, y), cv2.FONT_HERSHEY_SIMPLEX, small_font_scale, (255, 255, 255), font_thickness)
        
        # Right column sensors (if there's space)
        if w > 400:
            cv2.putText(frame, f"IR: {self.sensor_data['ir_left']},{self.sensor_data['ir_right']}", 
                       (150, y - 15), cv2.FONT_HERSHEY_SIMPLEX, small_font_scale, (255, 255, 255), font_thickness)
            cv2.putText(frame, f"Volt: {self.sensor_data['battery_voltage']}", 
                       (150, y), cv2.FONT_HERSHEY_SIMPLEX, small_font_scale, (255, 255, 255), font_thickness)
        
        # Instructions (bottom, smaller)
        instructions = "[c]LED [d]raw [f]ull [q]uit"
        cv2.putText(frame, instructions, (10, h - 10), cv2.FONT_HERSHEY_SIMPLEX, small_font_scale, (200, 200, 200), font_thickness)
    
    def cleanup(self):
        """Cleanup resources"""
        self.cap.release()
        cv2.destroyAllWindows()
        
        try:
            self.rover.set_motor_speeds(0, 0)
            print("Motors stopped")
        except Exception as e:
            print(f"Error during cleanup: {e}")
        
        print("Shutdown complete")


if __name__ == "__main__":
    print("Direct testing not supported - use through rover.py")