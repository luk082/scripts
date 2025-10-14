import cv2
import numpy as np
import mediapipe as mp
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import pickle
import time
import os
import sys
import contextlib

mp_hands = mp.solutions.hands
_ = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

class HandGestureRecognizer:
    def __init__(self):
        # Initialize MediaPipe hands
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        self.mp_draw = mp.solutions.drawing_utils
        
        # Initialize classifier with better parameters
        self.model = RandomForestClassifier(
            n_estimators=200,
            max_depth=20,
            min_samples_split=5,
            random_state=42
        )
        self.gesture_names = []
        
        # Systematic collection prompts
        self.collection_prompts = [
            # Distance variations
            (0, "Hold your hand at NORMAL distance from camera"),
            (5, "Move hand CLOSER to camera (20cm closer)"),
            (10, "Move hand FARTHER from camera (40cm away)"),
            (15, "Back to NORMAL distance"),
            
            # Angle variations
            (20, "Tilt hand 15 deg to the LEFT"),
            (25, "Tilt hand 15 deg to the RIGHT"),
            (30, "Tilt hand 15 deg UP"),
            (35, "Tilt hand 15 deg DOWN"),
            (40, "Return to NEUTRAL angle"),
            
            # Position variations
            (45, "Move hand to LEFT side of frame"),
            (50, "Move hand to RIGHT side of frame"),
            (55, "Move hand to TOP of frame"),
            (60, "Move hand to BOTTOM of frame"),
            (65, "CENTER your hand in frame"),
            
            # Rotation variations
            (70, "Rotate hand 30 deg CLOCKWISE"),
            (75, "Rotate hand 30 deg COUNTER-CLOCKWISE"),
            (80, "Return to STRAIGHT position"),
            
            # Lighting and final variations
            (85, "Slightly CURL/RELAX your fingers"),
            (90, "Make gesture slightly TIGHTER"),
            (95, "Make gesture slightly LOOSER"),
            (100, "Final samples - vary naturally"),
        ]
    
    def extract_landmarks(self, hand_landmarks):
        """Extract normalized landmark coordinates with better normalization"""
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
        
        # Add additional features: distances and angles
        normalized = np.array(normalized)
        
        # Calculate palm size for scale normalization
        palm_size = np.linalg.norm(landmarks[0:3] - landmarks[9:12])
        if palm_size > 0:
            normalized = normalized / palm_size
        
        # Add finger tip distances from wrist (shape features)
        finger_tips = [4, 8, 12, 16, 20]  # Thumb, Index, Middle, Ring, Pinky
        for tip_idx in finger_tips:
            tip_pos = landmarks[tip_idx*3:tip_idx*3+3]
            distance = np.linalg.norm(tip_pos - wrist)
            if palm_size > 0:
                normalized = np.append(normalized, distance / palm_size)
            else:
                normalized = np.append(normalized, distance)
        
        return normalized.tolist()
    
    def get_current_prompt(self, count):
        """Get the current collection prompt based on sample count"""
        for threshold, prompt in reversed(self.collection_prompts):
            if count >= threshold:
                return prompt
        return self.collection_prompts[0][1]
    
    def collect_training_data(self, gesture_name, num_samples=105):
        """Collect training data with systematic prompts"""
        cap = cv2.VideoCapture(0)
        samples = []
        count = 0
        last_capture_time = 0
        min_capture_interval = 0.3  # Minimum 300ms between captures
        
        print(f"\n{'='*60}")
        print(f"Collecting data for gesture: {gesture_name}")
        print(f"{'='*60}")
        print("INSTRUCTIONS:")
        print("- Follow the prompts that appear every 5 samples")
        print("- Press SPACE to capture (wait for green 'READY')")
        print("- Press 'q' to finish early")
        print("- Take your time and follow instructions carefully")
        print(f"{'='*60}\n")
        
        current_prompt = self.get_current_prompt(0)
        
        while count < num_samples:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(rgb_frame)
            
            # Calculate if enough time has passed since last capture
            current_time = time.time()
            can_capture = (current_time - last_capture_time) > min_capture_interval
            
            # Draw hand landmarks
            hand_detected = False
            if results.multi_hand_landmarks:
                hand_detected = True
                for hand_landmarks in results.multi_hand_landmarks:
                    self.mp_draw.draw_landmarks(
                        frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS
                    )
            
            # Get current prompt
            current_prompt = self.get_current_prompt(count)
            
            # Calculate progress bar
            progress = int((count / num_samples) * 100)
            bar_length = 40
            filled = int((progress / 100) * bar_length)
            bar = '█' * filled + '░' * (bar_length - filled)
            
            # Display info with better formatting
            y_pos = 30
            line_height = 35
            
            # Title
            cv2.rectangle(frame, (0, 0), (frame.shape[1], 60), (0, 0, 0), -1)
            cv2.putText(frame, f"GESTURE: {gesture_name.upper()}", (10, y_pos),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)
            
            y_pos += line_height + 10
            
            # Progress
            cv2.putText(frame, f"Progress: {count}/{num_samples} ({progress}%)", (10, y_pos),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            y_pos += line_height - 5
            
            y_pos += line_height + 5
            
            # Current instruction (highlighted)
            prompt_lines = self.wrap_text(current_prompt, 50)
            cv2.rectangle(frame, (5, y_pos - 25), (frame.shape[1] - 5, y_pos + len(prompt_lines) * 25 + 5), (50, 50, 50), -1)
            cv2.rectangle(frame, (5, y_pos - 25), (frame.shape[1] - 5, y_pos + len(prompt_lines) * 25 + 5), (0, 255, 255), 2)
            
            for i, line in enumerate(prompt_lines):
                cv2.putText(frame, line, (15, y_pos + i * 25),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            
            y_pos += len(prompt_lines) * 25 + 20
            
            # Status indicator
            if hand_detected and can_capture:
                status_text = "READY - Press SPACE"
                status_color = (0, 255, 0)
            elif hand_detected and not can_capture:
                status_text = "Wait..."
                status_color = (0, 165, 255)
            else:
                status_text = "NO HAND DETECTED"
                status_color = (0, 0, 255)
            
            cv2.putText(frame, status_text, (10, y_pos),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)
            
            cv2.imshow('Systematic Gesture Training', frame)
            
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord(' ') and hand_detected and can_capture:
                # Capture sample
                landmarks = self.extract_landmarks(results.multi_hand_landmarks[0])
                samples.append(landmarks)
                count += 1
                last_capture_time = current_time
                print(f"✓ Captured sample {count}/{num_samples} - {current_prompt}")
            elif key == ord('q'):
                print("\nEarly termination requested.")
                break
        
        cap.release()
        cv2.destroyAllWindows()
        
        print(f"\n{'='*60}")
        print(f"Completed! Collected {len(samples)} samples for '{gesture_name}'")
        print(f"{'='*60}\n")
        
        return samples
    
    def wrap_text(self, text, max_chars):
        """Wrap text to multiple lines"""
        words = text.split()
        lines = []
        current_line = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) + 1 <= max_chars:
                current_line.append(word)
                current_length += len(word) + 1
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
                current_length = len(word)
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
    
    def train_model(self, gesture_data):
        """Train the classifier on collected data"""
        X = []
        y = []
        
        for gesture_name, samples in gesture_data.items():
            X.extend(samples)
            y.extend([gesture_name] * len(samples))
        
        X = np.array(X)
        y = np.array(y)
        
        print(f"\nTraining data shape: {X.shape}")
        print(f"Total samples: {len(X)}")
        print(f"Samples per gesture:")
        for gesture in gesture_data.keys():
            print(f"  - {gesture}: {len(gesture_data[gesture])}")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Train model
        print("\n" + "="*60)
        print("Training model...")
        print("="*60)
        self.model.fit(X_train, y_train)
        
        # Evaluate
        train_accuracy = self.model.score(X_train, y_train)
        test_accuracy = self.model.score(X_test, y_test)
        
        print(f"\nTraining accuracy: {train_accuracy * 100:.2f}%")
        print(f"Testing accuracy:  {test_accuracy * 100:.2f}%")
        
        if train_accuracy - test_accuracy > 0.15:
            print("Warning: Large gap between train/test accuracy suggests overfitting")
        elif test_accuracy > 0.90:
            print("✓ Excellent accuracy achieved!")
        elif test_accuracy > 0.80:
            print("✓ Good accuracy - should work well")
        else:
            print("Consider collecting more diverse samples")
        
        self.gesture_names = list(gesture_data.keys())
        
        return test_accuracy
    
    def save_model(self, filename='gesture_model2.pkl'):
        """Save trained model to file"""
        with open(filename, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'gesture_names': self.gesture_names
            }, f)
        print(f"\n✓ Model saved to {filename}")
    
    def load_model(self, filename='gesture_model2.pkl'):
        """Load trained model from file"""
        if os.path.exists(filename):
            with open(filename, 'rb') as f:
                data = pickle.load(f)
                self.model = data['model']
                self.gesture_names = data['gesture_names']
            print(f"✓ Model loaded from {filename}")
            return True
        return False
    
    def recognize_gesture(self):
        """Real-time gesture recognition with improved visualization"""
        cap = cv2.VideoCapture(0)
        
        print("\n" + "="*60)
        print("Starting real-time gesture recognition...")
        print("="*60)
        print("Press 'q' to quit\n")
        
        # For smoothing predictions
        prediction_history = []
        history_length = 5
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(rgb_frame)
            
            gesture_text = "No hand detected"
            confidence = 0
            
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    # Draw landmarks
                    self.mp_draw.draw_landmarks(
                        frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS
                    )
                    
                    # Extract landmarks and predict
                    landmarks = self.extract_landmarks(hand_landmarks)
                    landmarks = np.array(landmarks).reshape(1, -1)
                    
                    prediction = self.model.predict(landmarks)[0]
                    confidence = np.max(self.model.predict_proba(landmarks))
                    
                    # Smooth predictions
                    prediction_history.append(prediction)
                    if len(prediction_history) > history_length:
                        prediction_history.pop(0)
                    
                    # Use most common prediction in history
                    if len(prediction_history) >= 3:
                        from collections import Counter
                        smoothed_prediction = Counter(prediction_history).most_common(1)[0][0]
                        prediction = smoothed_prediction
                    
                    gesture_text = f"{prediction}"
            
            # Display with better visualization
            # Background box for text
            box_height = 80
            cv2.rectangle(frame, (0, 0), (frame.shape[1], box_height), (0, 0, 0), -1)
            
            # Gesture name
            cv2.putText(frame, gesture_text, (10, 50),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)
            
            # Confidence bar
            if confidence > 0:
                bar_width = int(confidence * 300)
                bar_color = (0, 255, 0) if confidence > 0.7 else (0, 165, 255) if confidence > 0.5 else (0, 0, 255)
                cv2.rectangle(frame, (frame.shape[1] - 320, 20), (frame.shape[1] - 320 + bar_width, 40), bar_color, -1)
                cv2.rectangle(frame, (frame.shape[1] - 320, 20), (frame.shape[1] - 20, 40), (255, 255, 255), 2)
                cv2.putText(frame, f"{confidence*100:.0f}%", (frame.shape[1] - 320, 60),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            cv2.imshow('Hand Gesture Recognition', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()


# Example usage
if __name__ == "__main__":
    recognizer = HandGestureRecognizer()
    
    # Define gestures you want to recognize
    gestures = ['x+', 'x-', 'y+', 'y-', 'n']
    
    # Choose mode
    print("\n" + "="*60)
    print("SYSTEMATIC HAND GESTURE RECOGNIZER")
    print("="*60)
    print("\n1. Train new model (unavailable)")
    print("2. Load existing model and recognize")
    print("\nTIP: For best results, train with 100+ samples per gesture")
    print("     following the systematic prompts carefully.")
    choice = input("\nEnter choice (2 only atm): ")
    
    if choice == '1':
        # Collect training data
        gesture_data = {}
        
        print("\n" + "="*60)
        print(f"You will collect samples for {len(gestures)} gestures:")
        for i, gesture in enumerate(gestures, 1):
            print(f"  {i}. {gesture}")
        print("="*60)
        input("\nPress ENTER when ready to start...")
        
        for i, gesture in enumerate(gestures, 1):
            print(f"\n[{i}/{len(gestures)}] Preparing to collect gesture: {gesture}")
            input("Press ENTER to begin collection for this gesture...")
            
            samples = recognizer.collect_training_data(gesture, num_samples=105)
            if samples:
                gesture_data[gesture] = samples
            else:
                print(f"Warning: No samples collected for {gesture}")
        
        if gesture_data:
            # Train model
            recognizer.train_model(gesture_data)
            
            # Save model
            recognizer.save_model()
            
            # Ask if user wants to test
            test_choice = input("\nWould you like to test the model now? (y/n): ")
            if test_choice.lower() == 'y':
                recognizer.recognize_gesture()
        else:
            print("\nNo training data collected. Exiting.")
    
    elif choice == '2': # Change back to elif
        # Load existing model
        if recognizer.load_model():
            recognizer.recognize_gesture()
        else:
            print("No saved model found. Please train a model first.")