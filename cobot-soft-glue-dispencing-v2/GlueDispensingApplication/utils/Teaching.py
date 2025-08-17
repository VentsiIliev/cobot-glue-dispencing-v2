import cv2
import numpy as np
from GlueDispensingApplication.utils import utils
""" UTILS FOR CREATING WORKPIECE FUNCTION"""


def calculateMinHeightToFitObjectIntoFOV(contour, initial_pos, ppm_x, ppm_y, realWorldWidth, realWorldHeight,
                                         objectWidthOffset,
                                         objectHeightOffset, minAllowedHeight, maxAllowedHeight, heightOffset,
                                         debug=False):
    """
    Compute the required height to fit the detected object fully within the camera frame.
    """

    """DEBUG SECTION"""
    if debug:
        contourCopy = np.array(contour, dtype=np.int32)  # Convert to int32 if not already
        contourCopy = contourCopy.reshape((-1, 1, 2))  # Reshape to the correct format if necessary

        canvas = np.zeros((720, 1280, 3), dtype="uint8")
        cv2.drawContours(canvas, [contourCopy], -1, (255, 255, 255), -1)
        cv2.imshow("canvas", canvas)
        cv2.waitKey(0)
    """END OF DEBUG SECTION"""

    if contour is None or len(contour) == 0:
        return initial_pos[2]  # No contours detected, maintain current height

    # Find the largest contour
    _, _, object_width_px, object_height_px = cv2.boundingRect(contour)

    # Convert detected object size to real-world size (estimate)
    object_width_mm = object_width_px / ppm_x
    object_height_mm = object_height_px / ppm_y

    """DEBUG SECTION"""
    if debug:
        x, y, object_width_px, object_height_px = cv2.boundingRect(contour)
        # draw the bounding box
        cv2.rectangle(canvas, (x, y), (x + object_width_px, y + object_height_px), (0, 255, 0), 2)
        # put text with the width and height
        cv2.putText(canvas, f"{object_width_px} x {object_height_px}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                    (0, 255, 0), 2)
        # put text with the width and height in mm
        cv2.putText(canvas, f"{object_width_mm:.2f} x {object_height_mm:.2f}", (x, y - 30), cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 0), 2)
        cv2.imshow("canvas", canvas)
        cv2.waitKey(0)
    """END OF DEBUG SECTION"""

    object_width_mm += objectWidthOffset
    object_height_mm += objectHeightOffset

    # Ensure object fits within the frame at new height
    required_height_x = initial_pos[2] * (object_width_mm / realWorldWidth)
    required_height_y = initial_pos[2] * (object_height_mm / realWorldHeight)

    # Use the larger height to ensure full visibility
    required_height = max(required_height_x, required_height_y)

    # Prevent excessive height changes
    min_allowed_height = minAllowedHeight  # Prevent crashing into the object
    max_allowed_height = maxAllowedHeight  # Set a more reasonable limit

    adjusted_height = max(min_allowed_height, min(required_height, max_allowed_height))

    """DEBUG SECTION"""
    if debug:
        print(f"Object Size (px): {object_width_px} x {object_height_px}")
        print(f"Object Size (mm): {object_width_mm:.2f} x {object_height_mm:.2f}")
        print(f"Calculated Height: {adjusted_height} mm")
        print(f"Calculated Height+offset: {adjusted_height + heightOffset} mm")
    """END OF DEBUG SECTION"""

    return adjusted_height + heightOffset


def calculateTcpToImageCenterOffsets(imageCenter, robotX, robotY, cameraToRobotMatrix):
    """THIS FUNCTION IS USED TO CALCULATE THE OFFSETS BETWEEN THE ROBOT TCP AND THE IMAGE CENTER"""
    transformedImageCenter = utils.applyTransformation(cameraToRobotMatrix, [imageCenter])[0][0]
    transformedImageCenter = transformedImageCenter[0]
    offsets = robotX - transformedImageCenter[0], robotY - transformedImageCenter[1]

    return offsets
