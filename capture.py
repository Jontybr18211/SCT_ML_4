import cv2

def get_video_capture(src=0, width=640, height=480):
    cap = cv2.VideoCapture(src)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    return cap