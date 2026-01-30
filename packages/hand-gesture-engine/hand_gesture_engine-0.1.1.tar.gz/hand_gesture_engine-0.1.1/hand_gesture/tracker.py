#tracker.py

"""
This file conatins the code for core tracking class and their functionality.
"""

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from importlib.resources import files



class HandTracker:
    def __init__(self, model_path, max_hands=2, mirror=True, backend="CPU"):

        self.mirror = mirror
        
        self.backend = backend.upper()
        
        if model_path is None:
            model_path = files("hand_gesture.assets").joinpath("hand_landmarker.task")    

        # -------- GPU selection --------
        if backend == "AUTO":
            try:
                delegate = python.BaseOptions.Delegate.GPU
            except Exception:
                delegate = python.BaseOptions.Delegate.CPU

        elif backend == "GPU":
            delegate = python.BaseOptions.Delegate.GPU
        else:
            delegate = python.BaseOptions.Delegate.CPU
        
        
        base_options = python.BaseOptions(
            model_asset_path=str(model_path),
            delegate=delegate
        )


        base_options = python.BaseOptions(
            model_asset_path = str(model_path)
        )

        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=max_hands
        )

        self.detector = vision.HandLandmarker.create_from_options(options)
    
    def process(self, frame):
        if self.mirror:
            frame = cv2.flip(frame, 1)

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=frame_rgb
        )

        result = self.detector.detect(mp_image)
        
        handedness = None
        if result.handedness:
            # Example: 'Left' or 'Right'
            handedness = result.handedness[0][0].category_name

        return frame, result.hand_landmarks, handedness
