from micromelon import *
import cv2
import numpy as np
import pickle
import mediapipe as mp
import time
import sys

# ============================================================================
# UI CONFIGURATION - Adjust all visual elements here
# ============================================================================

# Window Configuration
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
WINDOW_NAME = "v2.3"
FULLSCREEN_MODE = True

# Color Bank (BGR format for OpenCV)
class UIColors:
    # Basic colors
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
    
    # UI Specific colors
    BACKGROUND = (0, 0, 0)
    TEXT_PRIMARY = (0, 255, 255)
    TEXT_SECONDARY = (0, 255, 0)
    TEXT_INACTIVE = (0, 0, 255)
    TEXT_ERROR = (0, 0, 255)
    BAR_BACKGROUND = (50, 50, 50)
    BAR_HIGH = (0, 255, 0)
    BAR_LOW = (0, 165, 255)
    BAR_BORDER = (255, 255, 255)
    INSTRUCTION_TEXT = (0, 255, 0)

# Font Configuration
FONT = cv2.FONT_HERSHEY_SIMPLEX
TITLE_FONT_SCALE = 1.0
TITLE_FONT_THICKNESS = 2
MAIN_FONT_SCALE = 0.9
MAIN_FONT_THICKNESS = 2
SMALL_FONT_SCALE = 0.8
SMALL_FONT_THICKNESS = 2

# Layout Configuration
MARGIN_LEFT = 10
MARGIN_TOP = 30
MARGIN_RIGHT = 20
MARGIN_BOTTOM = 30
LINE_SPACING = 10
SECTION_SPACING = 20
TEXT_PADDING = 5

# Title Section
TITLE_TEXT = "gestures v2.3"
TITLE_COLOR = UIColors.WHITE
TITLE_BG_COLOR = UIColors.BACKGROUND

# Gesture Display
GESTURE_ACTIVE_COLOR = UIColors.WHITE
GESTURE_INACTIVE_COLOR = UIColors.TEXT_INACTIVE
GESTURE_BG_COLOR = UIColors.BACKGROUND

# Confidence Bar
CONFIDENCE_BAR_WIDTH = 200
CONFIDENCE_BAR_HEIGHT = 20
CONFIDENCE_BAR_BG = UIColors.BAR_BACKGROUND
CONFIDENCE_BAR_HIGH = UIColors.BAR_HIGH
CONFIDENCE_BAR_LOW = UIColors.BAR_LOW
CONFIDENCE_BAR_BORDER = UIColors.BAR_BORDER
CONFIDENCE_THRESHOLD = 0.7  # Threshold for color change
CONFIDENCE_TEXT_COLOR = UIColors.WHITE

# Motor Status
MOTOR_TEXT_COLOR = UIColors.WHITE
MOTOR_BG_COLOR = UIColors.BACKGROUND

# LED Status
LED_TEXT_COLOR = UIColors.WHITE
LED_BG_COLOR = UIColors.BACKGROUND

# Sensor Section
SENSOR_TITLE_COLOR = UIColors.WHITE
SENSOR_TITLE_BG = UIColors.BACKGROUND
SENSOR_TEXT_COLOR = UIColors.WHITE
SENSOR_BG_COLOR = UIColors.BACKGROUND

# Instructions (Bottom Right)
INSTRUCTION_TEXT_COLOR = UIColors.WHITE
INSTRUCTION_BG_COLOR = UIColors.BACKGROUND
INSTRUCTION_SPACING = 30
INSTRUCTION_PADDING = 5

# ============================================================================
# END OF UI CONFIGURATION
# ============================================================================

# Initialize MediaPipe
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)
mp_draw = mp.solutions.drawing_utils

# Load the trained gesture model
print("loading model...")
try:
    with open('gesture_model.pkl', 'rb') as f:
        model_data = pickle.load(f)
        model = model_data['model']
        gesture_names = model_data['gesture_names']
    print(f"model loaded with gestures: {gesture_names}")
except Exception as e:
    print(f"error loading model: {e}")
    print("make sure 'gesture_model.pkl' is in the same directory")
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

# Set webcam resolution
cap.set(cv2.CAP_PROP_FRAME_WIDTH, WINDOW_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, WINDOW_HEIGHT)

# Color definitions for LEDs
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

# Sensor data storage
sensor_data = {
    'ultrasonic': 'n/a',
    'battery_percentage': 'n/a',
    'battery_voltage': 'n/a',
    'ir_left': 'n/a',
    'ir_right': 'n/a'
}

last_sensor_update = 0
sensor_update_interval = 0.5  # Update sensors every 0.5 seconds

# Gesture prediction with smoothing
prediction_history = []
history_length = 5

def extract_landmarks(hand_landmarks):
    """Extract normalized landmark coordinates (same as trainer)"""
    landmarks = []
    
    # Get all 21 landmark coordinates
    for landmark in hand_landmarks.landmark:
        landmarks.extend([landmark.x, landmark.y, landmark.z])
    
    landmarks = np.array(landmarks)
    
    # Normalize relative to wrist (landmark 0)
    wrist = landmarks[0:3]
    normalized = []
    
    for i in range(0, len(landmarks), 3):
        point = landmarks[i:i+3]
        normalized.extend(point - wrist)
    
    normalized = np.array(normalized)
    
    # Calculate palm size for scale normalization
    palm_size = np.linalg.norm(landmarks[0:3] - landmarks[9:12])
    if palm_size > 0:
        normalized = normalized / palm_size
    
    # Add finger tip distances from wrist
    finger_tips = [4, 8, 12, 16, 20]  # Thumb, Index, Middle, Ring, Pinky
    for tip_idx in finger_tips:
        tip_pos = landmarks[tip_idx*3:tip_idx*3+3]
        distance = np.linalg.norm(tip_pos - wrist)
        if palm_size > 0:
            normalized = np.append(normalized, distance / palm_size)
        else:
            normalized = np.append(normalized, distance)
    
    return normalized.tolist()

def update_sensors():
    """Update sensor readings from rover"""
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

def draw_text_with_background(frame, text, position, font=FONT, 
                               font_scale=MAIN_FONT_SCALE, text_color=UIColors.TEXT_SECONDARY, 
                               bg_color=UIColors.BACKGROUND, thickness=MAIN_FONT_THICKNESS, 
                               padding=TEXT_PADDING):
    """Draw text with a background rectangle"""
    text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
    x, y = position
    
    # Draw background rectangle
    cv2.rectangle(frame, 
                  (x - padding, y - text_size[1] - padding),
                  (x + text_size[0] + padding, y + padding),
                  bg_color, -1)
    
    # Draw text
    cv2.putText(frame, text, (x, y), font, font_scale, text_color, thickness)
    
    return y + text_size[1] + padding * 2

def gesture_to_motor_command(gesture):
    """Convert gesture name to motor commands"""
    # Map gesture names to motor commands
    gesture_map = {
        'x+': (30, 30),    # Forward - both motors forward
        'x-': (0, 0),  # Backward - both motors backward
        'y+': (-10, 10),   # Left - left motor back, right forward
        'y-': (10, -10),   # Right - left motor forward, right back
        'n': (-30, -30)        # Neutral/Stop - no movement
    }
    
    return gesture_map.get(gesture, (0, 0))

# Create window with appropriate settings
if FULLSCREEN_MODE:
    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
else:
    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_AUTOSIZE)

print("\n" + "="*60)
print("gestureControl")
print("="*60)
print("controls:")
print("  - use hand gestures to control the rover")
print("  - press 'c' to cycle LED colors")
print("  - press 'f' to toggle fullscreen")
print("  - press 'q' or 'esc' to quit")
print("="*60 + "\n")

# Main loop
running = True
current_gesture = "none"
gesture_confidence = 0.0
control_active = False

try:
    while running:
        current_time = time.time()
        
        # Update sensors periodically
        if current_time - last_sensor_update >= sensor_update_interval:
            update_sensors()
            last_sensor_update = current_time
        
        # Capture frame
        ret, frame = cap.read()
        if not ret:
            print("error reading frame")
            break
        
        # Flip frame horizontally for mirror effect
        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process hand landmarks
        results = hands.process(rgb_frame)
        
        left_motor = 0
        right_motor = 0
        
        if results.multi_hand_landmarks:
            control_active = True
            for hand_landmarks in results.multi_hand_landmarks:
                # Draw hand landmarks
                mp_draw.draw_landmarks(
                    frame, hand_landmarks, mp_hands.HAND_CONNECTIONS
                )
                
                # Extract landmarks and predict
                landmarks = extract_landmarks(hand_landmarks)
                landmarks_array = np.array(landmarks).reshape(1, -1)
                
                prediction = model.predict(landmarks_array)[0]
                confidence = np.max(model.predict_proba(landmarks_array))
                
                # Smooth predictions
                prediction_history.append(prediction)
                if len(prediction_history) > history_length:
                    prediction_history.pop(0)
                
                # Use most common prediction in history
                if len(prediction_history) >= 3:
                    from collections import Counter
                    smoothed_prediction = Counter(prediction_history).most_common(1)[0][0]
                    prediction = smoothed_prediction
                
                current_gesture = prediction
                gesture_confidence = confidence
                
                # Convert gesture to motor commands
                left_motor, right_motor = gesture_to_motor_command(current_gesture)
        else:
            control_active = False
            current_gesture = "no hand"
            gesture_confidence = 0.0
            prediction_history.clear()
        
        # Apply motor control
        Motors.write(left_motor, right_motor)
        
        # Draw UI overlay
        overlay_y = MARGIN_TOP
        
        # Title
        overlay_y = draw_text_with_background(
            frame, TITLE_TEXT, (MARGIN_LEFT, overlay_y),
            font_scale=TITLE_FONT_SCALE, text_color=TITLE_COLOR, 
            thickness=TITLE_FONT_THICKNESS, bg_color=TITLE_BG_COLOR
        )
        
        overlay_y += LINE_SPACING
        
        # Gesture info
        gesture_color = GESTURE_ACTIVE_COLOR if control_active else GESTURE_INACTIVE_COLOR
        overlay_y = draw_text_with_background(
            frame, f"gesture: {current_gesture.upper()}", (MARGIN_LEFT, overlay_y),
            text_color=gesture_color, bg_color=GESTURE_BG_COLOR
        )
        
        # Confidence bar
        if gesture_confidence > 0:
            # Background
            cv2.rectangle(frame, (MARGIN_LEFT, overlay_y), 
                         (MARGIN_LEFT + CONFIDENCE_BAR_WIDTH, overlay_y + CONFIDENCE_BAR_HEIGHT),
                         CONFIDENCE_BAR_BG, -1)
            
            # Filled bar
            confidence_filled = int(gesture_confidence * CONFIDENCE_BAR_WIDTH)
            bar_color = CONFIDENCE_BAR_HIGH if gesture_confidence > CONFIDENCE_THRESHOLD else CONFIDENCE_BAR_LOW
            cv2.rectangle(frame, (MARGIN_LEFT, overlay_y), 
                         (MARGIN_LEFT + confidence_filled, overlay_y + CONFIDENCE_BAR_HEIGHT),
                         bar_color, -1)
            
            # Border
            cv2.rectangle(frame, (MARGIN_LEFT, overlay_y), 
                         (MARGIN_LEFT + CONFIDENCE_BAR_WIDTH, overlay_y + CONFIDENCE_BAR_HEIGHT),
                         CONFIDENCE_BAR_BORDER, 2)
            
            # Percentage text
            conf_text = f"{gesture_confidence*100:.0f}%"
            cv2.putText(frame, conf_text, 
                       (MARGIN_LEFT + CONFIDENCE_BAR_WIDTH + 10, overlay_y + 15),
                       FONT, SMALL_FONT_SCALE, CONFIDENCE_TEXT_COLOR, SMALL_FONT_THICKNESS)
            
            overlay_y += CONFIDENCE_BAR_HEIGHT + LINE_SPACING * 2
        
        overlay_y += LINE_SPACING
        
        # Motor status
        overlay_y = draw_text_with_background(
            frame, f"motors: {left_motor}, {right_motor}", (MARGIN_LEFT, overlay_y),
            text_color=MOTOR_TEXT_COLOR, bg_color=MOTOR_BG_COLOR
        )
        
        # LED color
        overlay_y = draw_text_with_background(
            frame, f"LED: {color_names[current_color_index]}", (MARGIN_LEFT, overlay_y),
            text_color=LED_TEXT_COLOR, bg_color=LED_BG_COLOR
        )
        
        overlay_y += SECTION_SPACING
        
        # Sensor data
        overlay_y = draw_text_with_background(
            frame, "sensors", (MARGIN_LEFT, overlay_y),
            text_color=SENSOR_TITLE_COLOR, bg_color=SENSOR_TITLE_BG
        )
        
        overlay_y = draw_text_with_background(
            frame, f"ultrasonic: {sensor_data['ultrasonic']}", (MARGIN_LEFT, overlay_y),
            font_scale=SMALL_FONT_SCALE, thickness=SMALL_FONT_THICKNESS,
            text_color=SENSOR_TEXT_COLOR, bg_color=SENSOR_BG_COLOR
        )
        overlay_y = draw_text_with_background(
            frame, f"battery: {sensor_data['battery_percentage']} ({sensor_data['battery_voltage']})",
            (MARGIN_LEFT, overlay_y), font_scale=SMALL_FONT_SCALE, thickness=SMALL_FONT_THICKNESS,
            text_color=SENSOR_TEXT_COLOR, bg_color=SENSOR_BG_COLOR
        )
        overlay_y = draw_text_with_background(
            frame, f"IR: {sensor_data['ir_left']}, {sensor_data['ir_right']}",
            (MARGIN_LEFT, overlay_y), font_scale=SMALL_FONT_SCALE, thickness=SMALL_FONT_THICKNESS,
            text_color=SENSOR_TEXT_COLOR, bg_color=SENSOR_BG_COLOR
        )
        
        # Instructions (bottom right)
        instructions = [
            "[c]ycle LED colour",
            "toggle [f]ullscreen",
            "[q]uit/esc"
        ]
        
        for i, instr in enumerate(instructions):
            text_size = cv2.getTextSize(instr, FONT, SMALL_FONT_SCALE, SMALL_FONT_THICKNESS)[0]
            x = frame.shape[1] - text_size[0] - MARGIN_RIGHT
            y = frame.shape[0] - MARGIN_BOTTOM - (len(instructions) - i - 1) * INSTRUCTION_SPACING
            
            cv2.rectangle(frame, 
                         (x - INSTRUCTION_PADDING, y - text_size[1] - INSTRUCTION_PADDING),
                         (x + text_size[0] + INSTRUCTION_PADDING, y + INSTRUCTION_PADDING), 
                         INSTRUCTION_BG_COLOR, -1)
            cv2.putText(frame, instr, (x, y), FONT,
                       SMALL_FONT_SCALE, INSTRUCTION_TEXT_COLOR, SMALL_FONT_THICKNESS)
        
        # Show frame
        cv2.imshow(WINDOW_NAME, frame)
        
        # Handle keyboard input
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q') or key == 27:  # 'q' or ESC
            running = False
        elif key == ord('c'):  # Change LED color
            current_color_index = (current_color_index + 1) % len(color_list)
            try:
                LEDs.writeAll(color_list[current_color_index].value)
                print(f"LED colour changed to {color_names[current_color_index]}")
            except Exception as e:
                print(f"error changing LED colour: {e}")
        elif key == ord('f'):  # Toggle fullscreen
            # global FULLSCREEN_MODE
            FULLSCREEN_MODE = not FULLSCREEN_MODE
            if FULLSCREEN_MODE:
                cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
                print("fullscreen mode enabled")
            else:
                cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)
                print("fullscreen mode disabled")
        
        time.sleep(0.05)  # Small delay to prevent overload

except KeyboardInterrupt:
    print("\nkeyboard interrupt")

finally:
    # Cleanup
    print("\nshutting down...")
    cap.release()
    cv2.destroyAllWindows()
    
    try:
        Motors.write(0, 0)  # Stop motors
        LEDs.off()
    except Exception as e:
        print(f"error during cleanup: {e}")
    
    rc.stopRover()
    rc.end()
    print("shutdown complete")