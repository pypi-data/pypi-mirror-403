#util.py

"""
This file contains other utility programs. (i.e. Extra functionality)
"""

import cv2

#to draw landmarks on on the screen (hand)
def draw_landmarks(frame, hand_landmarks):
    for lm in hand_landmarks:
        h,w,_ = frame.shape
        cv2.circle(frame, (int(lm.x*w), int(lm.y*h)), 5, (0,255,0), -1)