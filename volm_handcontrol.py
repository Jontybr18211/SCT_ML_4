import cv2
import time
import numpy as np
import math
import mediapipe as mp
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

#  Hand Tracking Module 

class HandDetector():
    
    # Finds Hands in a BGR image using the MediaPipe Hands solution.
    
    def __init__(self, static_image_mode=False, max_num_hands=1, min_detection_confidence=0.7, min_tracking_confidence=0.5):
        
        """
        Initializes the hand detector.
        :param static_image_mode: Whether to treat images as a video stream or static images.
        :param max_num_hands: Maximum number of hands to detect.
        :param min_detection_confidence: Minimum confidence for hand detection.
        :param min_tracking_confidence: Minimum confidence for landmark tracking.
        """
        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands(
            static_image_mode=static_image_mode,
            max_num_hands=max_num_hands,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
            )
        self.mpDraw = mp.solutions.drawing_utils
        self.tipIds = [4, 8, 12, 16, 20]

    def find_hands(self, img, draw=True):
        # Finds all hands in an image and draws landmarks.
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(img_rgb)
        if self.results.multi_hand_landmarks:
            for hand_lms in self.results.multi_hand_landmarks:
                if draw:
                    self.mpDraw.draw_landmarks(img, hand_lms, self.mpHands.HAND_CONNECTIONS)
        return img

    def find_position(self, img, hand_no=0, draw=True):
        # Finds landmarks of a specific hand and returns their positions and a bounding box.
        x_list, y_list = [], []
        self.lm_list = []
        bbox = []
        if self.results.multi_hand_landmarks:
            my_hand = self.results.multi_hand_landmarks[hand_no]
            for id, lm in enumerate(my_hand.landmark):
                h, w, c = img.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                x_list.append(cx)
                y_list.append(cy)
                self.lm_list.append([id, cx, cy])
                if draw:
                    cv2.circle(img, (cx, cy), 5, (255, 0, 255), cv2.FILLED)
            if x_list and y_list:
                xmin, xmax = min(x_list), max(x_list)
                ymin, ymax = min(y_list), max(y_list)
                bbox = xmin, ymin, xmax, ymax
                if draw:
                    cv2.rectangle(img, (bbox[0] - 20, bbox[1] - 20),
                                  (bbox[2] + 20, bbox[3] + 20), (0, 255, 0), 2)
        return self.lm_list, bbox

    def fingers_up(self):
        # Checks which fingers are extended.
        fingers = []
        if not self.lm_list:
            return []
        # Thumb (checks x-axis)
        if self.lm_list[self.tipIds[0]][1] > self.lm_list[self.tipIds[0] - 1][1]:
            fingers.append(1)
        else:
            fingers.append(0)
        # 4 Fingers (checks y-axis)
        for id in range(1, 5):
            if self.lm_list[self.tipIds[id]][2] < self.lm_list[self.tipIds[id] - 2][2]:
                fingers.append(1)
            else:
                fingers.append(0)
        return fingers

    def find_distance(self, p1, p2, img, draw=True):
        """Finds the distance between two points."""
        x1, y1 = self.lm_list[p1][1], self.lm_list[p1][2]
        x2, y2 = self.lm_list[p2][1], self.lm_list[p2][2]
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        length = math.hypot(x2 - x1, y2 - y1)
        if draw:
            cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 3)
            cv2.circle(img, (x1, y1), 10, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (x2, y2), 10, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (cx, cy), 10, (0, 0, 255), cv2.FILLED)
        return length, img, [x1, y1, x2, y2, cx, cy]


# Main Application Logic

def main():
    
    wCam, hCam = 640, 480
    cap = cv2.VideoCapture(0) # Use 0 for default webcam
    if not cap.isOpened():
        print("Error: Could not open video stream.")
        return
    cap.set(3, wCam)
    cap.set(4, hCam)
    pTime = 0

    detector = HandDetector(max_num_hands=1, min_detection_confidence=0.7)

    # Windows Volume Control Setup 
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    vol_bar = 400
    vol_per = 0
    color_vol = (255, 0, 0)

    while True:
        success, img = cap.read()
        if not success:
            break

        # Hand Detection
        img = detector.find_hands(img)
        lm_list, bbox = detector.find_position(img, draw=True)

        if len(lm_list) != 0:
            # Filter based on hand size/distance
            area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1]) // 100
            if 250 < area < 1000:
                # Find Distance between Thumb and Index Finger
                length, img, line_info = detector.find_distance(4, 8, img)

                # Convert distance to volume percentage
                vol_bar = np.interp(length, [50, 200], [400, 150])
                vol_per = np.interp(length, [50, 200], [0, 100])

                # Smooth the volume change
                smoothness = 10
                vol_per = smoothness * round(vol_per / smoothness)

                #  Check for activation gesture (pinky down) 
                fingers = detector.fingers_up()
                if fingers and not fingers[4]: # If pinky is down
                    volume.SetMasterVolumeLevelScalar(vol_per / 100, None)
                    cv2.circle(img, (line_info[4], line_info[5]), 15, (0, 255, 0), cv2.FILLED)
                    color_vol = (0, 255, 0) # Green for active
                else:
                    color_vol = (255, 0, 0) # Red for inactive
        
        # UI
        cv2.rectangle(img, (50, 150), (85, 400), (255, 0, 0), 3)
        cv2.rectangle(img, (50, int(vol_bar)), (85, 400), (255, 0, 0), cv2.FILLED)
        cv2.putText(img, f'{int(vol_per)} %', (40, 450), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 0, 0), 3)
        
        # Display current system volume
        c_vol = int(volume.GetMasterVolumeLevelScalar() * 100)
        cv2.putText(img, f'Vol Set: {c_vol}', (400, 50), cv2.FONT_HERSHEY_COMPLEX, 1, color_vol, 3)

        # Frame Rate Display
        cTime = time.time()
        fps = 1 / (cTime - pTime)
        pTime = cTime
        cv2.putText(img, f'FPS: {int(fps)}', (40, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 0, 0), 3)

        cv2.imshow("Volume Control", img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()