#config.py

"""
This is the configuration file where we can move all hard-coded values like:
-confidence thresholds
-stabilizer timings
-pinch distance
-finger tolerance
into one central config object.
"""


from dataclasses import dataclass
import yaml
from pathlib import Path


@dataclass
class GestureConfig:
    # --- Stabilizer ---
    hold_time: float = 0.35          # seconds gesture must stay stable
    min_confidence: float = 0.6      # confidence threshold

    # --- Gesture thresholds ---
    pinch_threshold: float = 0.04
    thumb_distance_threshold: float = 0.25

    # --- Engine behavior ---
    mirror: bool = True
    
    # --- Stability frames ---
    stability_frames: int = 5
    
     # -------- Runtime / Backend --------
    use_gpu: bool = False 
    
    #yaml configuration
    @classmethod
    def from_yaml(cls, path: str):
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        with open(path, "r") as f:
            data = yaml.safe_load(f) or {}

        # Flatten nested YAML safely
        return cls(
            use_gpu=data.get("backend", cls.use_gpu),

            hold_time=data.get("stability", {}).get("hold_time", cls.hold_time),
            min_confidence=data.get("stability", {}).get("min_confidence", cls.min_confidence),

            pinch_threshold=data.get("thresholds", {}).get("pinch", cls.pinch_threshold),
            thumb_distance_threshold=data.get("thresholds", {}).get("thumb_extended", cls.thumb_distance_threshold),
        )