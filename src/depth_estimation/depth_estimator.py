'''
"""Depth Anything V2 Depth Estimation Module"""

import cv2
import numpy as np
import torch
import torch.nn.functional as F


class DepthEstimator:
    """Depth estimation using Depth Anything V2"""
    
    def __init__(self, model_type: str = "vits", device: str = "cuda"):
        """
        Initialize depth estimator
        
        Args:
            model_type: Model size (vits, vitb, vitl)
            device: Device to run on (cuda or cpu)
        """
        self.device = device
        self.model_type = model_type
        self.depth_model = None
        self.transform = None
        
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize Depth Anything V2 model"""
        # TODO: Implement model loading from Depth Anything V2
        # This requires downloading from HuggingFace or official repo
        pass
    
    def estimate_depth(self, frame: np.ndarray) -> np.ndarray:
        """
        Estimate depth map from frame
        
        Args:
            frame: Input image frame
            
        Returns:
            Depth map
        """
        # TODO: Implement depth estimation
        # Placeholder returning zeros
        return np.zeros((frame.shape[0], frame.shape[1]), dtype=np.float32)
    
    def get_depth_at_point(self, depth_map: np.ndarray, x: int, y: int, 
                          window_size: int = 5) -> float:
        """
        Get depth value at specific point
        
        Args:
            depth_map: Depth estimation map
            x: X coordinate
            y: Y coordinate
            window_size: Window size for averaging
            
        Returns:
            Depth value in meters
        """
        h, w = depth_map.shape
        x1 = max(0, x - window_size // 2)
        x2 = min(w, x + window_size // 2)
        y1 = max(0, y - window_size // 2)
        y2 = min(h, y + window_size // 2)
        
        region = depth_map[y1:y2, x1:x2]
        return np.mean(region) if region.size > 0 else 0.0
    
    def visualize_depth(self, depth_map: np.ndarray) -> np.ndarray:
        """
        Visualize depth map
        
        Args:
            depth_map: Depth estimation map
            
        Returns:
            Colored depth visualization
        """
        depth_normalized = cv2.normalize(depth_map, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        depth_colored = cv2.applyColorMap(depth_normalized, cv2.COLORMAP_TURBO)
        return depth_colored
'''
# ==========================================
# LIVE DEPTH DASHBOARD
# Depth-Anything-V2 + OpenCV
# macOS ready: live RGB + depth dashboard
# This script opens the default webcam, runs a depth-estimation
# model on each frame and displays RGB and depth side-by-side.
# You can quit by pressing 'q' in the OpenCV window or by typing
# 'q' followed by Enter in the terminal where the script runs.
# ==========================================

import cv2                # OpenCV: capture images, display windows, image processing
import torch               # PyTorch: used to check CUDA availability for model device selection
import numpy as np         # NumPy: array operations and conversions
from transformers import pipeline  # Hugging Face pipeline to load the depth model
from PIL import Image      # Pillow: convert OpenCV arrays (RGB) into PIL images for the model
import threading           # Threading: background thread to listen for terminal input
import sys                 # sys.stdin: read lines typed in the terminal


# ------------------------------------------
# Device Selection
# ------------------------------------------
# Choose device for the pipeline: 0 refers to the first CUDA GPU for Hugging Face pipeline,
# and -1 tells the pipeline to use the CPU.
device = 0 if torch.cuda.is_available() else -1
print("Running on:", "GPU" if device == 0 else "CPU")


# ------------------------------------------
# Load Depth Model
# ------------------------------------------
# The Hugging Face pipeline will load the model specified by `checkpoint`.
# `task="depth-estimation"` tells transformers to configure the pipeline for depth.
checkpoint = "depth-anything/Depth-Anything-V2-base-hf"
pipe = pipeline(
    task="depth-estimation",  # pipeline task name
    model=checkpoint,          # which model to load
    device=device              # which device to run on (GPU=0 or CPU=-1)
)


# ------------------------------------------
# Initialize Webcam (macOS fixed)
# ------------------------------------------
# Use OpenCV's VideoCapture to get frames from the default camera (index 0).
# On macOS we explicitly request the AVFoundation backend via cv2.CAP_AVFOUNDATION
# so that the camera is accessed correctly on macOS systems.
cap = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)  # macOS AVFoundation backend

# If the camera could not be opened, raise an error — there's nothing to do without a camera.
if not cap.isOpened():
    raise RuntimeError("Could not open webcam.")

print("Webcam opened successfully. Press 'q' to exit.")


# ------------------------------------------
# Terminal listener (type 'q' + Enter to quit from the terminal)
# ------------------------------------------
# We create an Event that can be set from another thread to signal the main loop to stop.
stop_event = threading.Event()


def terminal_listener():
    """Listen on stdin in a background thread and set stop_event when user types 'q' and Enter.

    Behavior notes:
    - This reads full lines from sys.stdin. The user must press Enter after typing.
    - If the read fails or an exception occurs, we set the stop event so the program can
      terminate cleanly instead of hanging.
    """
    try:
        # Iterate over lines from stdin. This will block until a line is entered.
        for line in sys.stdin:
            # If an empty string is returned, stdin has been closed; break out.
            if not line:
                break
            # Strip whitespace and compare lowercased input to 'q'. If matched, signal stop.
            if line.strip().lower() == 'q':
                stop_event.set()
                break
    except Exception:
        # If anything goes wrong while reading stdin, set stop_event to avoid hanging.
        stop_event.set()


# Start listener thread as a daemon so it won't prevent process exit if main thread ends.
threading.Thread(target=terminal_listener, daemon=True).start()


# Optional: check available cameras (commented out). Useful for debugging multiple camera setups.
# for i in range(4):
#     test_cap = cv2.VideoCapture(i, cv2.CAP_AVFOUNDATION)
#     if test_cap.isOpened():
#         print(f"Camera {i} is available")
#         test_cap.release()


# ------------------------------------------
# Create OpenCV Window
# ------------------------------------------
# Define the window name and create a resizable window. We set the window to be
# topmost so it appears above other windows on screen; adjust or remove if undesired.
window_name = "Depth Dashboard (RGB | Depth)"
cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
cv2.resizeWindow(window_name, 1280, 480)  # initial window size (width x height)
cv2.setWindowProperty(window_name, cv2.WND_PROP_TOPMOST, 1)  # keep window on top


# ------------------------------------------
# Main Loop
# ------------------------------------------
# The loop captures frames, runs the depth estimation model on each frame, and displays
# the original RGB frame and a colored depth map side-by-side.
while True:
    # Allow external stop via terminal input. If the background listener set the event,
    # break out of the loop and begin cleanup.
    if stop_event.is_set():
        break

    # Read a single frame from the webcam. ret is a boolean (True if success), frame is the image.
    ret, frame = cap.read()
    # If reading failed, print a message and break the loop so we can cleanup resources.
    if not ret:
        print("Failed to capture frame from webcam.")
        break

    # Resize the captured frame to a known resolution for consistent model input and display.
    # This keeps compute and memory usage predictable.
    frame = cv2.resize(frame, (640, 480))

    # OpenCV uses BGR color ordering by default; convert to RGB which is expected by PIL and many models.
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Convert the NumPy RGB array to a PIL Image which the Hugging Face pipeline expects.
    pil_img = Image.fromarray(frame_rgb)

    # Run the depth estimation pipeline on the PIL image. The pipeline returns a dict-like object
    # with a 'depth' entry that contains the per-pixel depth values (usually floating point).
    prediction = pipe(pil_img)
    depth = np.array(prediction["depth"])  # convert the model output to a NumPy array

    # Normalize depth values to the 0-255 range and convert to uint8 for OpenCV visualization.
    # cv2.normalize scales the values based on min/max so depth maps are visible regardless of range.
    depth_norm = cv2.normalize(depth, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

    # Apply a colormap to the normalized depth map to make depth variations visible as colors.
    # COLORMAP_INFERNO gives a visually pleasing, perceptually-uniform color ramp.
    depth_colormap = cv2.applyColorMap(depth_norm, cv2.COLORMAP_INFERNO)

    # Stack the original BGR frame (left) and the depth colormap (right) horizontally.
    # Note: `frame` is still in BGR ordering which is fine for OpenCV display.
    combined = np.hstack((frame, depth_colormap))

    # Show the combined image in the named window. This call updates the GUI window.
    cv2.imshow(window_name, combined)

    # Check for key presses in the OpenCV window. waitKey(1) waits 1 millisecond for a key event
    # and returns its ASCII code if pressed. If the user presses 'q' while the window has focus,
    # exit the loop. The bitmasking (& 0xFF) ensures compatibility across platforms.
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break


# ------------------------------------------
# Cleanup
# ------------------------------------------
# Release the VideoCapture so other applications can use the webcam, and destroy OpenCV windows.
cap.release()
cv2.destroyAllWindows()
print("Dashboard closed.")