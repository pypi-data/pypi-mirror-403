#recognizer.py
"""
This file works as the brain for gesture recognition.
It checks which gesture is made and returns (gesture_name, confidence).
"""

import logging
from .gestures import *

logger = logging.getLogger(__name__)



def recognize_gesture(hand, config):
    # Returns: (gesture_name: str, confidence: float)
    logger.debug("Starting gesture recognition")

    if is_thumbs_up(hand, config):
        logger.info("Gesture detected: THUMBS UP")
        return "THUMBS UP", 1.0

    if is_peace(hand):
        logger.info("Gesture detected: PEACE")
        return "PEACE", 1.0
    
    if is_ok(hand, config):
        logger.info("Gesture detected: OK")
        return "OK", 1.0

    gesture, confidence = is_three_fingers(hand)
    if gesture:
        logger.info(f"Gesture detected: {gesture}")
        return gesture, confidence

    if is_fist(hand, config):
        logger.info("Gesture detected: FIST")
        return "FIST", 1.0

    if is_thumbs_down(hand, config):
        logger.info("Gesture detected: THUMBS DOWN")
        return "THUMBS DOWN", 1.0

    if is_open_hand(hand):
        logger.info("Gesture detected: OPEN HAND")
        return "OPEN HAND", 1.0
        
    if is_pinch(hand, config):
        logger.info("Gesture detected: PINCH")
        return "PINCH", 0.9
    
    if is_pointing(hand):
        logger.info("Gesture detected: POINTING")
        return "POINTING", 1.0
    
    logger.debug("No gesture matched")
    return "UNKNOWN", 0.0
