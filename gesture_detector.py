import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import cv2
from utils import draw_landmarks

class GestureDetector:
    """
    A class to detect hand gestures using MediaPipe's Gesture Recognizer model.
    
    Attributes:
        recognizer: The MediaPipe GestureRecognizer instance for gesture detection.
    """
    
    def __init__(self, model_path="gesture_recognizer.task"):
        """
        Initialize the GestureDetector with the specified model path.
        
        Args:
            model_path (str): Path to the pre-trained gesture recognizer model file.
                             Defaults to "gesture_recognizer.task".
        """
        # Define MediaPipe task components
        BaseOptions = mp.tasks.BaseOptions
        GestureRecognizer = mp.tasks.vision.GestureRecognizer
        GestureRecognizerOptions = mp.tasks.vision.GestureRecognizerOptions
        VisionRunningMode = mp.tasks.vision.RunningMode

        # Configure the recognizer options
        options = GestureRecognizerOptions(
            base_options=BaseOptions(model_asset_path=model_path),
            running_mode=VisionRunningMode.IMAGE,  # Process single images (frames)
            num_hands=1  # Detect gestures from one hand
        )
        
        # Create the gesture recognizer instance
        self.recognizer = GestureRecognizer.create_from_options(options)

    def process(self, frame):
        """
        Process a frame to detect hand gestures and landmarks.
        
        Args:
            frame: A NumPy array representing the input image in BGR format.
        
        Returns:
            tuple: (annotated_frame, landmarks, gesture)
                - annotated_frame: The input frame with hand landmarks drawn.
                - landmarks: A list of hand landmarks as (x, y, z) tuples, or empty if none detected.
                - gesture: The detected gesture label (e.g., "Closed_Fist"), or "None" if no gesture.
        """
        # Convert the frame to MediaPipe's Image format (SRGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
        
        # Perform gesture recognition
        recognition_result = self.recognizer.recognize(mp_image)

        # Extract the gesture label
        if recognition_result.gestures and recognition_result.gestures[0]:
            gesture = recognition_result.gestures[0][0].category_name
        else:
            gesture = "None"

        # Extract and process hand landmarks
        if recognition_result.hand_landmarks and recognition_result.hand_landmarks[0]:
            landmarks = recognition_result.hand_landmarks[0]
            # Convert landmarks to a list of (x, y, z) tuples
            landmarks = [(lm.x, lm.y, lm.z) for lm in landmarks]
            # Draw landmarks on the frame using the utils function
            frame = draw_landmarks(frame, landmarks, connections=mp.solutions.hands.HAND_CONNECTIONS)
        else:
            landmarks = []

        # Return the annotated frame, landmarks, and gesture label
        return frame, [landmarks] if landmarks else [], gesture