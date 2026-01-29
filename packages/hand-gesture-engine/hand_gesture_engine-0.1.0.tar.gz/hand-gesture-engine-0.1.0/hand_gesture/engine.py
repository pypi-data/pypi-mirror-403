#engine.py

"""
This is an engine for the 'hand_gesture' library(user)
This will encapsulate all the complexity and the backend processes and only provide us what we need.
It is for abstration.
"""

from .tracker import HandTracker
from .recognizer import recognize_gesture
from .stabilizer import GestureStabilizer
from .utils import draw_landmarks
from .config import GestureConfig
from importlib.resources import files




class GestureEngine:
    def __init__(self, max_hands=2, backend="AUTO", config: GestureConfig = GestureConfig()):
        self.config = config
        
        self.backend = backend.upper()
        
        if backend == "AUTO":
            backend = "GPU" if config.use_gpu else "CPU"
        
        self.stability_threshold = config.stability_frames 
        
        model_path = files("hand_gesture.assets").joinpath("hand_landmarker.task")
        
        self.tracker = HandTracker(
                    model_path=model_path,
                    max_hands=max_hands,
                    mirror=config.mirror,
                    backend=self.backend
        )
        
        self.stabilizer = GestureStabilizer(
            hold_time=config.hold_time,
            min_confidence=config.min_confidence
        )
        

    def process(self, frame):
        """
        Input:
            OpenCV BGR frame

        Output:
            frame (processed)
            stable gesture name or None
        """
        frame, hands, handedness = self.tracker.process(frame)

        if not hands:
            self.stabilizer.update("UNKNOWN")
            return frame, None

        # draw landmarks on frame
        for hand in hands:
            draw_landmarks(frame, hand)

        gesture, confidence= recognize_gesture(hands[0], self.config)
        
        stable = self.stabilizer.update(gesture, confidence)

        return frame, stable

