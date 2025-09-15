"""Age Detector Stub for testing PeekShield integration.

This stub alternates minor/adult status for testing and also supports
manual toggle by pressing 'm' to mark as minor, 'a' for adult.

For production, replace with real age detection logic that POSTS to /update.
"""
import cv2
import requests
import time
import threading

AGE_SERVICE_UPDATE_URL = "http://127.0.0.1:5001/update"

def post_status(is_minor, age_estimate):
    payload = {"is_minor": bool(is_minor), "age_estimate": age_estimate, "last_seen": time.strftime("%Y-%m-%d %H:%M:%S")}
    try:
        requests.post(AGE_SERVICE_UPDATE_URL, json=payload, timeout=0.5)
    except Exception as e:
        print("Could not update age service:", e)

def camera_loop():
    cap = cv2.VideoCapture(0)
    is_minor = False
    age_est = None
    print("Camera stub running. Press 'm' to mark minor, 'a' to mark adult, 'q' to quit.")
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        cv2.imshow("Age Detector Stub - Press m/a", frame)
        k = cv2.waitKey(1) & 0xFF
        if k == ord('m'):
            is_minor = True
            age_est = 14
            post_status(is_minor, age_est)
            print("Posted: minor")
        elif k == ord('a'):
            is_minor = False
            age_est = 25
            post_status(is_minor, age_est)
            print("Posted: adult")
        elif k == ord('q'):
            break
        # optional: continuously post status every 5 seconds
        time.sleep(0.05)
    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    camera_loop()