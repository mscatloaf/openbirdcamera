import io
import logging
import socketserver
import time
import datetime
import os
import numpy as np
import cv2
from http import server
from threading import Condition, Thread

from picamera2 import Picamera2
from picamera2.encoders import JpegEncoder
from picamera2.outputs import FileOutput

WIDTH = 2028
HEIGHT = 1080

# --- CONFIGURATION ---
SAVE_DIR = "/opt/birdcam/images"
MOTION_THRESHOLD_RATIO = 0.001
PIXEL_SENSITIVITY = 10
SAVE_COOLDOWN = 5  # Seconds to wait between saves

# Ensure the directory exists
try:
    os.makedirs(SAVE_DIR, exist_ok=True)
except PermissionError:
    print(f"Error: No permission to write to {SAVE_DIR}. Try running with sudo.")
    exit(1)

PAGE = """...""" # (Keep your existing HTML here)

class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()

def detect_motion(output):
    """Background thread to analyze the stream for motion."""
    avg_frame = None
    
    print(f"Motion detection active. Saving to {SAVE_DIR}")
    while True:
        with output.condition:
            output.condition.wait()
            frame_data = output.frame

        if frame_data is None:
            continue

        nparr = np.frombuffer(frame_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
        
        # Analysis processing
        small_img = cv2.resize(img, (640, 360))
        blurred = cv2.GaussianBlur(small_img, (21, 21), 0)

        if avg_frame is None:
            avg_frame = blurred.copy().astype("float")
            continue

        cv2.accumulateWeighted(blurred, avg_frame, 0.5)
        frame_delta = cv2.absdiff(blurred, cv2.convertScaleAbs(avg_frame))
        thresh = cv2.threshold(frame_delta, PIXEL_SENSITIVITY, 255, cv2.THRESH_BINARY)[1]
        motion_percent = np.count_nonzero(thresh) / thresh.size

        if motion_percent > MOTION_THRESHOLD_RATIO:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"{timestamp}.jpg"
            filepath = os.path.join(SAVE_DIR, filename)
            
            with open(filepath, "wb") as f:
                f.write(frame_data)
            
            print(f"Motion detected ({motion_percent:.2%})! Saved: {filename}")
            
            # This enforces the 3-second limit between captures
            time.sleep(SAVE_COOLDOWN)

# --- (Rest of the script remains identical) ---

class StreamingHandler(server.BaseHTTPRequestHandler):
    # ... (unchanged)
    pass

class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    # ... (unchanged)
    pass

picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(main={"size": (WIDTH, HEIGHT)}))
output = StreamingOutput()
picam2.start_recording(JpegEncoder(), FileOutput(output))

motion_thread = Thread(target=detect_motion, args=(output,), daemon=True)
motion_thread.start()

try:
    address = ('', 8000)
    server = StreamingServer(address, StreamingHandler)
    server.serve_forever()
finally:
    picam2.stop_recording()
