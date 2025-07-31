import cv2
import tkinter as tk
import pyautogui
from tkinter import filedialog, messagebox
from capture import get_video_capture
from gesture_detector import GestureDetector

# Initialize gesture detector
gesture_detector = GestureDetector(model_path="gesture_recognizer.task")

SCREEN_W, SCREEN_H = pyautogui.size()
is_clicking = False

def process_hand_frame(frame):
    """
    Process a frame to detect gestures and draw landmarks.
    
    Args:
        frame: Input frame in BGR format.
    
    Returns:
        frame: Annotated frame with gesture label and landmarks.
    """
    frame, hands, gesture = gesture_detector.process(frame)
    if hands and gesture != "None":
        cv2.putText(frame, f"{gesture}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    return frame

def handle_image():
    """
    Handle image input for gesture recognition.
    """
    path = filedialog.askopenfilename(filetypes=[('Image', '*.png;*.jpg')])
    if not path:
        return
    img = cv2.imread(path)
    if img is None:
        messagebox.showerror('Error', f'Cannot load image: {path}')
        return
    annotated = process_hand_frame(img)
    cv2.imshow('Image', annotated)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def handle_video():
    """
    Handle video input for gesture recognition.
    """
    path = filedialog.askopenfilename(filetypes=[('Video', '*.mp4;*.avi')])
    if not path:
        return
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        messagebox.showerror('Error', f'Cannot open video: {path}')
        return
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        annotated = process_hand_frame(frame)
        cv2.imshow('Video', annotated)
        if cv2.waitKey(1) == 27:  # ESC to exit
            break
    cap.release()
    cv2.destroyAllWindows()

def handle_camera():
    """
    Handle live camera input for gesture recognition with mouse control.
    """
    global is_clicking
    cap = get_video_capture()
    if cap is None or not cap.isOpened():
        messagebox.showerror('Error', 'Cannot access camera')
        return
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        # Flip the frame for mirror-like effect
        frame = cv2.flip(frame, 1)
        frame, hands, gesture = gesture_detector.process(frame)
        if hands and gesture != "None":
            lm = hands[0]  # Use first hand's landmarks
            # Mouse control logic
            if gesture == "Pointing_Up":
                x, y, _ = lm[8]  # Index fingertip
                pyautogui.moveTo(int(x * SCREEN_W), int(y * SCREEN_H))
                is_clicking = False
            elif gesture == "Closed_Fist" and not is_clicking:
                pyautogui.click()
                is_clicking = True
            else:
                is_clicking = False
            # Display gesture label
            cv2.putText(frame, gesture, (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.imshow('Camera', frame)
        if cv2.waitKey(1) == 27:  # ESC to exit
            break
    cap.release()
    cv2.destroyAllWindows()

def main():
    """
    Main function to create and run the Tkinter GUI.
    """
    root = tk.Tk()
    root.title('Hand Gesture Recognition')
    for txt, cmd in [('Upload Image', handle_image),
                     ('Upload Video', handle_video),
                     ('Open Camera', handle_camera),
                     ('Exit', root.quit)]:
        tk.Button(root, text=txt, width=20, command=cmd).pack(pady=5)
    root.mainloop()

if __name__ == '__main__':
    main()