#gestures.py

"""
Reusable hand gesture detection functions.
All public gesture functions accept `hand`.
"""

import math
import logging




logger = logging.getLogger(__name__)


# ---------- HELPERS ----------
def _most_fingers_folded(lm, min_folded=3):
    folded = 0
    for tip, mcp in [(8,5), (12,9), (16,13), (20,17)]:
        if lm[tip].y > lm[mcp].y:
            folded += 1
    return folded >= min_folded


def _thumb_not_extended(lm):
    return _distance(lm[4], lm[0]) < 0.28  # slightly larger threshold


def _distance(a, b):
    return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)


def _other_fingers_extended(lm, min_extended=2):
    extended = 0
    for tip, pip in [(12,10), (16,14), (20,18)]:
        if lm[tip].y < lm[pip].y:  # finger mostly up
            extended += 1
    return extended >= min_extended


def _finger_extended(lm, tip, pip, tolerance=0.05):
    """
    Returns True if the finger is mostly extended.
    Allows some bending.
    """
    return (lm[pip].y - lm[tip].y) > tolerance


def _finger_folded(lm, tip, mcp):
    return lm[tip].y > lm[mcp].y


def finger_is_up(tip, pip, wrist_y):
    return tip.y < pip.y and tip.y < wrist_y


def _thumb_extended(lm, threshold):
    return _distance(lm[4], lm[0]) > threshold


def _other_fingers_folded(lm, min_folded=3):
    """
    Returns True if at least `min_folded` non-thumb fingers are folded.
    """
    folded = 0
    for tip, mcp in [(8,5), (12,9), (16,13), (20,17)]:
        if lm[tip].y > lm[mcp].y:
            folded += 1
    return folded >= min_folded


def _thumb_direction(lm):
    """
    Returns: 'UP', 'DOWN', or 'SIDE'
    """
    tip = lm[4]
    ip = lm[3]

    dx = tip.x - ip.x
    dy = ip.y - tip.y   # inverted y-axis

    angle = math.degrees(math.atan2(dy, dx))

    # Up: 60° to 120°
    if 60 <= angle <= 120:
        return "UP"

    # Down: -120° to -60°
    if -120 <= angle <= -60:
        return "DOWN"

    return "SIDE"



# ---------- BASIC GESTURES ----------

def is_fist(hand, config):
    lm = hand
    fingers_folded = _most_fingers_folded(lm, min_folded=3)

    # Thumb should NOT point down (prevent THUMBS DOWN override)
    thumb_not_extended = not _thumb_extended(lm, config.thumb_distance_threshold)
    thumb_direction = _thumb_direction(lm)
    result = fingers_folded and thumb_not_extended and thumb_direction != "DOWN"
    logger.debug(f"is_fist: {result}") #EXAMPLE FOR LOGGER
    return result


def is_open_hand(hand):
    lm = hand
    return all(
        _finger_extended(lm, tip, pip)
        for tip, pip in [(8,6), (12,10), (16,14), (20,18)]
    )




# ---------- FEW-FINGER GESTURES ----------

def is_pointing(hand):
    lm = hand
    return (
        _finger_extended(lm, 8, 6) and
        _finger_folded(lm, 12, 9) and
        _finger_folded(lm, 16, 13) and
        _finger_folded(lm, 20, 17)
    )


def is_peace(hand):
    lm = hand
    return (
        _finger_extended(lm, 8, 6) and
        _finger_extended(lm, 12, 10) and
        _finger_folded(lm, 16, 13) and
        _finger_folded(lm, 20, 17)
    )


def is_three_fingers(hand):
    lm = hand
    wrist_y = lm[0].y

    fingers = [
        finger_is_up(lm[8],  lm[6],  wrist_y),   # index
        finger_is_up(lm[12], lm[10], wrist_y),  # middle
        finger_is_up(lm[16], lm[14], wrist_y),  # ring
        finger_is_up(lm[20], lm[18], wrist_y),  # pinky
    ]

    count = sum(fingers)

    # Only return THREE if thumb is NOT pinching index
    dx = lm[4].x - lm[8].x
    dy = lm[4].y - lm[8].y
    distance = (dx*dx + dy*dy)**0.5

    if count == 3 and distance > 0.08:   # ignore pinch
        return "THREE", count / 4.0

    return None, 0.0





# ---------- THUMB GESTURES ----------

def is_thumbs_up(hand, config):
    lm = hand
    direction = _thumb_direction(lm)

    return (
        _thumb_extended(lm, config.thumb_distance_threshold) and
        _other_fingers_folded(lm) and
        direction == "UP"
    )


def is_thumbs_down(hand, config):
    lm = hand
    return (
        _thumb_extended(lm, config.thumb_distance_threshold) and
        _other_fingers_folded(lm, min_folded=3) and
        _thumb_direction(lm) == "DOWN"
    )




# ---------- PINCH / OK ----------

def is_pinch(hand, config):
    lm = hand
    dx = lm[4].x - lm[8].x
    dy = lm[4].y - lm[8].y
    distance = (dx*dx + dy*dy)**0.5
    return distance < config.pinch_threshold



def is_ok(hand, config):
    return (
        is_pinch(hand, config) and
        _other_fingers_extended(hand, min_extended=2)
    )


