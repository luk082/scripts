from micromelon import *
import cv2
import numpy as np
import pickle
import mediapipe as mp
import time
import sys

# ============================================================================
# PERFORMANCE CONFIGURATION
# ============================================================================

# Optimized resolution - balance between speed and accuracy
CAMERA_WIDTH = 640  # Reduced from 1280
CAMERA_HEIGHT = 480  # Reduced from 720

# Process every frame for maximum responsiveness
PROCESS_EVERY_N_FRAMES = 1  # Process every frame!

# Use fastest MediaPipe model
MP_MODEL_COMPLEXITY = 1  # 0=fastest, 1=balanced, 2=accurate

# Reduce hand landmark drawing complexity
DRAW_LANDMARKS = False  # Turn off landmark drawing for speed boost

# ============================================================================
# UI CONFIGURATION
# ============================================================================

WINDOW_NAME = "v2.3 FAST"
FULLSCREEN_MODE = True

class UIColors:
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    RED = (0, 0, 255)
    GREEN = (0, 255, 0)
    BLUE = (255, 0, 0)
    YELLOW = (0, 255, 255)
    CYAN = (255, 255, 0)
    MAGENTA = (255, 0, 255)
    ORANGE = (0, 165, 255)
    PURPLE = (255, 0, 128)
    LIME = (0, 255, 128)
    PINK = (203, 192, 255)
    
    BACKGROUND = (0, 0, 0)
    TEXT_PRIMARY = (0, 255, 255)
    TEXT_SECONDARY = (0, 255, 0)
    TEXT_INACTIVE = (0, 0, 255)
    BAR_BACKGROUND = (50, 50, 50)
    BAR_HIGH = (0, 255, 0)
    BAR_LOW = (0, 165, 255)
    BAR_BORDER = (255, 255, 255)

FONT = cv2.FONT_HERSHEY_SIMPLEX
TITLE_FONT_SCALE = 1.0
TITLE_FONT_THICKNESS = 2
MAIN_FONT_SCALE = 0.9
MAIN_FONT_THICKNESS = 2
SMALL_FONT_SCALE = 0.8
SMALL_FONT_THICKNESS = 2

MARGIN_LEFT = 10
MARGIN_TOP = 30
MARGIN_RIGHT = 20
MARGIN_BOTTOM = 30
LINE_SPACING = 10
SECTION_SPACING = 20
TEXT_PADDING = 5

TITLE_TEXT = "gestures v2.3 FAST"
TITLE_COLOR = UIColors.WHITE
GESTURE_ACTIVE_COLOR = UIColors.WHITE
GESTURE_INACTIVE_COLOR = UIColors.TEXT_INACTIVE

CONFIDENCE_BAR_WIDTH = 200
CONFIDENCE_BAR_HEIGHT = 20
CONFIDENCE_THRESHOLD = 0.7

# ============================================================================
# END OF UI CONFIGURATION
# ============================================================================

# Initialize MediaPipe with fastest settings
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    model_complexity=MP_MODEL_COMPLEXITY,
    min_detection_confidence=0.5,  # Lower threshold for faster detection
    min_tracking_confidence=0.5
)
mp_draw = mp.solutions.drawing_utils

# Load model
print("loading model...")
try:
    with open('gesture_model.pkl', 'rb') as f:
        model_data = pickle.load(f)
        model = model_data['model']
        gesture_names = model_data['gesture_names']
    print(f"model loaded with gestures: {gesture_names}")
except Exception as e:
    print(f"error loading model: {e}")
    sys.exit(1)

# Connect to rover
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

Robot.setName("gestureRover")
rc.startRover()

# Initialize webcam
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("webcam error")
    sys.exit(1)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
cap.set(cv2.CAP_PROP_FPS, 60)  # Request higher FPS
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize buffer lag

# LED colors
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

try:
    LEDs.writeAll(color_list[current_color_index].value)
except Exception as e:
    print(f"error setting initial LED colour: {e}")

# Sensor data
sensor_data = {
    'ultrasonic': 'n/a',
    'battery_percentage': 'n/a',
    'battery_voltage': 'n/a',
    'ir_left': 'n/a',
    'ir_right': 'n/a'
}

last_sensor_update = 0
sensor_update_interval = 2.0  # Update sensors infrequently

# Minimal smoothing for fast response
prediction_history = []
history_length = 2  # Only 2 frames for quick response

FINGER_TIPS = np.array([4, 8, 12, 16, 20])

def extract_landmarks(hand_landmarks):
    """Optimized landmark extraction using numpy"""
    landmarks = np.array([[lm.x, lm.y, lm.z] for lm in hand_landmarks.landmark])
    
    wrist = landmarks[0]
    normalized = landmarks - wrist
    normalized = normalized.flatten()
    
    palm_size = np.linalg.norm(landmarks[0] - landmarks[9])
    if palm_size > 0:
        normalized = normalized / palm_size
    
    # Vectorized finger tip distances
    for tip_idx in FINGER_TIPS:
        distance = np.linalg.norm(landmarks[tip_idx] - wrist)
        if palm_size > 0:
            normalized = np.append(normalized, distance / palm_size)
        else:
            normalized = np.append(normalized, distance)
    
    return normalized

def update_sensors():
    """Update sensor readings"""
    try:
        ultrasonic = Ultrasonic.read()
        sensor_data['ultrasonic'] = str(ultrasonic) if ultrasonic != 255 else 'N/A'
    except:
        sensor_data['ultrasonic'] = 'Error'
    
    try:
        sensor_data['battery_percentage'] = f"{Battery.readPercentage()}%"
        sensor_data['battery_voltage'] = f"{Battery.readVoltage()}V"
    except:
        sensor_data['battery_percentage'] = 'Error'
        sensor_data['battery_voltage'] = 'Error'
    
    try:
        sensor_data['ir_left'] = str(IR.readLeft())
        sensor_data['ir_right'] = str(IR.readRight())
    except:
        sensor_data['ir_left'] = 'Error'
        sensor_data['ir_right'] = 'Error'

# Pre-compute gesture map
GESTURE_MAP = {
    'x+': (30, 30),
    'x-': (-20, -20),
    'y+': (5, 10),
    'y-': (10, 5),
    'n': (0, 0)
}

def gesture_to_motor_command(gesture):
    """Convert gesture to motor commands"""
    return GESTURE_MAP.get(gesture, (0, 0))

# Create window
if FULLSCREEN_MODE:
    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
else:
    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_AUTOSIZE)

print("\n" + "="*60)
print("gestureControl FAST MODE")
print("="*60)
print("Optimizations:")
print("  - Lower resolution (640x480)")
print("  - Fastest MediaPipe model")
print("  - Minimal smoothing for quick response")
print("  - Landmark drawing disabled (press 'd' to toggle)")
print("\nControls:")
print("  - use hand gestures to control the rover")
print("  - press 'c' to cycle LED colors")
print("  - press 'd' to toggle landmark drawing")
print("  - press 'f' to toggle fullscreen")
print("  - press 'q' or 'esc' to quit")
print("="*60 + "\n")

# Main loop variables
running = True
current_gesture = "none"
gesture_confidence = 0.0
control_active = False

fps_start_time = time.time()
fps_frame_count = 0
current_fps = 0

# Pre-allocate arrays for speed
from collections import Counter

try:
    while running:
        current_time = time.time()
        
        # Update sensors infrequently
        if current_time - last_sensor_update >= sensor_update_interval:
            update_sensors()
            last_sensor_update = current_time
        
        # Capture frame
        ret, frame = cap.read()
        if not ret:
            print("error reading frame")
            break
        
        # Flip horizontally
        frame = cv2.flip(frame, 1)
        
        # Convert to RGB once
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process hand detection EVERY frame for responsiveness
        results = hands.process(rgb_frame)
        
        if results.multi_hand_landmarks:
            control_active = True
            hand_landmarks = results.multi_hand_landmarks[0]  # Only first hand
            
            # Draw landmarks only if enabled
            if DRAW_LANDMARKS:
                mp_draw.draw_landmarks(
                    frame, hand_landmarks, mp_hands.HAND_CONNECTIONS,
                    mp_draw.DrawingSpec(color=(0, 255, 0), thickness=1, circle_radius=2),
                    mp_draw.DrawingSpec(color=(255, 255, 255), thickness=1)
                )
            
            # Extract and predict
            landmarks = extract_landmarks(hand_landmarks)
            landmarks_array = landmarks.reshape(1, -1)
            
            prediction = model.predict(landmarks_array)[0]
            proba = model.predict_proba(landmarks_array)
            confidence = np.max(proba)
            
            # Minimal smoothing - only use last 2 predictions
            prediction_history.append(prediction)
            if len(prediction_history) > history_length:
                prediction_history.pop(0)
            
            # Quick majority vote
            if len(prediction_history) >= 2:
                smoothed_prediction = Counter(prediction_history).most_common(1)[0][0]
                prediction = smoothed_prediction
            
            current_gesture = prediction
            gesture_confidence = confidence
        else:
            control_active = False
            current_gesture = "no hand"
            gesture_confidence = 0.0
            prediction_history.clear()
        
        # Apply motor control immediately
        left_motor, right_motor = gesture_to_motor_command(current_gesture)
        Motors.write(left_motor, right_motor)
        
        # Calculate FPS
        fps_frame_count += 1
        if current_time - fps_start_time >= 1.0:
            current_fps = fps_frame_count / (current_time - fps_start_time)
            fps_frame_count = 0
            fps_start_time = current_time
        
        # ===== MINIMAL UI DRAWING =====
        y = MARGIN_TOP
        
        # Title with FPS
        cv2.putText(frame, f"{TITLE_TEXT} - {current_fps:.1f} FPS", 
                   (MARGIN_LEFT, y), FONT, TITLE_FONT_SCALE, TITLE_COLOR, TITLE_FONT_THICKNESS)
        y += 40
        
        # Gesture
        gesture_color = GESTURE_ACTIVE_COLOR if control_active else GESTURE_INACTIVE_COLOR
        cv2.putText(frame, f"gesture: {current_gesture.upper()}", 
                   (MARGIN_LEFT, y), FONT, MAIN_FONT_SCALE, gesture_color, MAIN_FONT_THICKNESS)
        y += 35
        
        # Confidence bar
        if gesture_confidence > 0:
            cv2.rectangle(frame, (MARGIN_LEFT, y), 
                         (MARGIN_LEFT + CONFIDENCE_BAR_WIDTH, y + CONFIDENCE_BAR_HEIGHT),
                         UIColors.BAR_BACKGROUND, -1)
            
            confidence_filled = int(gesture_confidence * CONFIDENCE_BAR_WIDTH)
            bar_color = UIColors.BAR_HIGH if gesture_confidence > CONFIDENCE_THRESHOLD else UIColors.BAR_LOW
            cv2.rectangle(frame, (MARGIN_LEFT, y), 
                         (MARGIN_LEFT + confidence_filled, y + CONFIDENCE_BAR_HEIGHT),
                         bar_color, -1)
            
            cv2.rectangle(frame, (MARGIN_LEFT, y), 
                         (MARGIN_LEFT + CONFIDENCE_BAR_WIDTH, y + CONFIDENCE_BAR_HEIGHT),
                         UIColors.BAR_BORDER, 2)
            
            cv2.putText(frame, f"{gesture_confidence*100:.0f}%", 
                       (MARGIN_LEFT + CONFIDENCE_BAR_WIDTH + 10, y + 15),
                       FONT, SMALL_FONT_SCALE, UIColors.WHITE, SMALL_FONT_THICKNESS)
            y += 35
        
        y += 10
        
        # Motors
        cv2.putText(frame, f"motors: {left_motor}, {right_motor}", 
                   (MARGIN_LEFT, y), FONT, MAIN_FONT_SCALE, UIColors.WHITE, MAIN_FONT_THICKNESS)
        y += 35
        
        # LED
        cv2.putText(frame, f"LED: {color_names[current_color_index]}", 
                   (MARGIN_LEFT, y), FONT, MAIN_FONT_SCALE, UIColors.WHITE, MAIN_FONT_THICKNESS)
        y += 45
        
        # Sensors (compact)
        cv2.putText(frame, "sensors", 
                   (MARGIN_LEFT, y), FONT, MAIN_FONT_SCALE, UIColors.WHITE, MAIN_FONT_THICKNESS)
        y += 30
        cv2.putText(frame, f"ultrasonic: {sensor_data['ultrasonic']}", 
                   (MARGIN_LEFT, y), FONT, SMALL_FONT_SCALE, UIColors.WHITE, SMALL_FONT_THICKNESS)
        y += 25
        cv2.putText(frame, f"battery: {sensor_data['battery_percentage']} ({sensor_data['battery_voltage']})",
                   (MARGIN_LEFT, y), FONT, SMALL_FONT_SCALE, UIColors.WHITE, SMALL_FONT_THICKNESS)
        y += 25
        cv2.putText(frame, f"IR: {sensor_data['ir_left']}, {sensor_data['ir_right']}",
                   (MARGIN_LEFT, y), FONT, SMALL_FONT_SCALE, UIColors.WHITE, SMALL_FONT_THICKNESS)
        
        # Instructions (bottom right) - simplified
        instructions = ["[c]LED [d]raw [f]ullscreen [q]uit"]
        text_size = cv2.getTextSize(instructions[0], FONT, SMALL_FONT_SCALE, SMALL_FONT_THICKNESS)[0]
        x = frame.shape[1] - text_size[0] - MARGIN_RIGHT
        y = frame.shape[0] - MARGIN_BOTTOM
        cv2.putText(frame, instructions[0], (x, y), FONT,
                   SMALL_FONT_SCALE, UIColors.WHITE, SMALL_FONT_THICKNESS)
        
        # Show frame
        cv2.imshow(WINDOW_NAME, frame)
        
        # Handle keyboard (non-blocking)
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q') or key == 27:
            running = False
        elif key == ord('c'):
            current_color_index = (current_color_index + 1) % len(color_list)
            try:
                LEDs.writeAll(color_list[current_color_index].value)
            except Exception as e:
                print(f"error changing LED colour: {e}")
        elif key == ord('d'):
            DRAW_LANDMARKS = not DRAW_LANDMARKS
            print(f"landmark drawing: {'ON' if DRAW_LANDMARKS else 'OFF'}")
        elif key == ord('f'):
            FULLSCREEN_MODE = not FULLSCREEN_MODE
            if FULLSCREEN_MODE:
                cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
            else:
                cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)

except KeyboardInterrupt:
    print("\nkeyboard interrupt")

finally:
    print("\nshutting down...")
    cap.release()
    cv2.destroyAllWindows()
    
    try:
        Motors.write(0, 0)
        LEDs.off()
    except Exception as e:
        print(f"error during cleanup: {e}")
    
    rc.stopRover()
    rc.end()
    print("shutdown complete")