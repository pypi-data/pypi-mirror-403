#stabilizer.py

"""
This is for gesture stabilizer.
The 'recognizer.py' file checks the gesture in every frame, which is not smooth as you have to make a perfect gesture for each of those frames for program to recognize.
So, what this file do, is that, rahter than checking each frame, we will first see if the gesture is made.
When made, we will first wait for some frames, idealy for the very next frame amd check if the same gesture continues.
If continues, "recognizer.py" will than process it, and if not, will wait for N-frames till the gesture continues.
"""

import time
from collections import deque


class GestureStabilizer:
    def __init__(self, hold_time=0.20, min_confidence=0.45):
        self.hold_time = hold_time
        self.min_confidence = min_confidence
        self.current_gesture = None
        self.start_time = None

    def update(self, gesture, confidence=1.0):
        now = time.time()

        if gesture is None or confidence < self.min_confidence:
            self.current_gesture = None
            self.start_time = None
            return None

        if gesture != self.current_gesture:
            self.current_gesture = gesture
            self.start_time = now
            return None

        if now - self.start_time >= self.hold_time:
            return gesture

        return None

