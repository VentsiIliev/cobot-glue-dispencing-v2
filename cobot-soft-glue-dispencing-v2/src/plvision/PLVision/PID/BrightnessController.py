"""
* File: PIDController.py
* Author: IlV
* Comments:
* Revision history:
* Date       Author      Description
* -----------------------------------------------------------------
** 100624     IlV         Initial release
* -----------------------------------------------------------------
*
"""

import cv2
import numpy as np

from ..PID.PIDController import PIDController


class BrightnessController(PIDController):
    def __init__(self, Kp, Ki, Kd, setPoint):
        super().__init__(Kp, Ki, Kd, setPoint)

    def calculateBrightness(self, frame):
        """
        Calculate the brightness of a frame.

        Args:
            frame (np.array): The frame to calculate the brightness of.

        Returns:
            float: The brightness of the frame.
        """
        # Convert the frame to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Calculate the mean brightness
        return cv2.mean(gray)[0]

    def adjustBrightness(self, frame, adjustment):
        """
        Adjust the brightness of a frame.

        Args:
            frame (np.array): The frame to adjust the brightness of.
            adjustment (float): The amount to adjust the brightness by.

        Returns:
            np.array: The frame with adjusted brightness.
        """
        # Clip the adjustment to the range [-100, 100]
        adjustment = np.clip(adjustment, -100, 100)

        # Adjust the brightness of the frame
        return cv2.convertScaleAbs(frame, alpha=1, beta=adjustment)