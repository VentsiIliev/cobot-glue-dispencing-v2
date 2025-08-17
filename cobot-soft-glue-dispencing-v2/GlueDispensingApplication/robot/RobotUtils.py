import cv2
import numpy as np

from GlueDispensingApplication.utils.utils import rotate_point

import cv2
import numpy as np


# def shrink(cnt, offset_distance):

#     """
#     Shrinks or expands a contour by a given offset distance.
#
#     Args:
#         cnt (numpy.ndarray): The input contour (Nx1x2 array of points).
#         offset_distance (float): The distance to shrink (negative) or expand (positive) the contour.
#
#     Returns:
#         numpy.ndarray: The modified contour.
#     """
#     # Create a blank image large enough to hold the contour
#     cnt = cnt.astype(np.int32)  # Ensure integer type
#     bounding_box = cv2.boundingRect(cnt)
#     width, height = bounding_box[2], bounding_box[3]
#     blank_image = np.zeros((height + 2 * abs(offset_distance), width + 2 * abs(offset_distance)), dtype=np.uint8)
#
#     # Draw the contour on the blank image
#     offset = abs(offset_distance)
#     shifted_cnt = cnt + offset  # Shift contour to avoid boundary issues
#     # cv2.drawContours(blank_image, [shifted_cnt], -1, 255, thickness=cv2.FILLED)
#
#     # Apply morphological operations to shrink or expand
#     kernel_size = int(abs(offset_distance))
#     kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
#     if offset_distance < 0:
#         # Shrink the contour
#         processed_image = cv2.erode(blank_image, kernel, iterations=1)
#     else:
#         # Expand the contour
#         processed_image = cv2.dilate(blank_image, kernel, iterations=1)
#
#     # Find the new contour
#     contours, _ = cv2.findContours(processed_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
#     if contours:
#         # Return the largest contour (in case multiple are found)
#         return max(contours, key=cv2.contourArea) - offset  # Shift back to original position
#     else:
#         return cnt  # Return the original contour if no valid contour is found

# def zigZag( contour, spacing):
# THIS FUNTION GENERATES POINTS ALONG THE LONGER SIDE OF THE CONTOUR BBOX WICH RESOLVES IN GENERATING MORE POINTS
# AND CAUSING THE ROBOT TO ACCELERATE AND DECELERATE MORE FREQUENTLY
# THIS IS WHY IT IS COMMENTED OUT AND USING THE FUNCTION BELOW INSTEAD!
# SHOULD CREATE 1 FUNCTION WICH TAKES A PARAMETER SETTING THE DIRECTION!

#     points = [tuple(point) for point in contour]
#     zigzag_coords = []
#
#     bbox = cv2.minAreaRect(np.array(points))
#     box = cv2.boxPoints(bbox)
#     center = np.mean(box, axis=0)  # More accurate center
#     width, height = bbox[1]
#     angle = bbox[2]
#
#     # if width < height:
#     #     width, height = height, width
#         # angle += 90
#
#     # # Adjust for vertical direction
#     # if direction == "vertical":
#     #     angle += 90
#
#     # Generate zigzag points in rotated space
#     direction = 1  # Start with positive direction
#     for i in range(0, int(width), spacing):
#         x_new = -width / 2 + i + center[0]  # Centered around bbox
#         y_top = -height / 2 + center[1]
#         y_bottom = height / 2 + center[1]
#
#         if direction == 1:
#             zigzag_coords.append((x_new, y_top))
#             zigzag_coords.append((x_new, y_bottom))
#         else:
#             zigzag_coords.append((x_new, y_bottom))
#             zigzag_coords.append((x_new, y_top))
#         direction *= -1  # Alternate direction
#
#     # Convert points to homogeneous coordinates for rotation
#     points = np.array(zigzag_coords, dtype=np.float32)
#     ones = np.ones((points.shape[0], 1))
#     points_homogeneous = np.hstack([points, ones])
#
#     # Compute rotation matrix
#     theta = np.radians(angle)
#     rotation_matrix = np.array([
#         [np.cos(theta), -np.sin(theta), center[0] - center[0] * np.cos(theta) + center[1] * np.sin(theta)],
#         [np.sin(theta), np.cos(theta), center[1] - center[0] * np.sin(theta) - center[1] * np.cos(theta)],
#         [0, 0, 1]
#     ])
#
#     # Apply rotation transformation
#     rotated_points = (rotation_matrix @ points_homogeneous.T).T[:, :2].astype(int)
#
#     # return [(float(x), float(y)) for x, y in rotated_points]
#     return rotated_points.reshape(-1, 1, 2).astype(np.int32)

def zigZag(contour, spacing):
    """
    Generate zigzag pattern within a contour boundary.

    Args:
        contour: Input contour in OpenCV format (N, 1, 2) or list of [x, y] points
        spacing: Distance between zigzag lines

    Returns:
        numpy.ndarray: Zigzag points in OpenCV format (N, 1, 2)
    """
    # Input validation and normalization
    if contour is None or len(contour) == 0:
        raise ValueError("Input contour is empty.")

    # Convert to numpy array and normalize shape
    arr = np.array(contour, dtype=np.float32)

    # Handle different input formats
    if arr.ndim == 3 and arr.shape[1] == 1 and arr.shape[2] == 2:
        # Already in OpenCV format (N, 1, 2)
        points = arr.reshape(-1, 2)
    elif arr.ndim == 2 and arr.shape[1] == 2:
        # List of [x, y] points (N, 2)
        points = arr
    elif arr.ndim == 2 and arr.shape[0] == 2:
        # Single point as [x, y] - reshape
        points = arr.T
    else:
        raise ValueError(f"Invalid contour shape: {arr.shape}. Expected (N, 2) or (N, 1, 2)")

    if len(points) < 3:
        raise ValueError("Contour must have at least 3 points for zigzag generation.")

    # Validate that points are numeric
    if not np.isfinite(points).all():
        raise ValueError("Contour contains invalid (NaN or infinite) values.")

    try:
        # Get minimum area rectangle
        bbox = cv2.minAreaRect(points.astype(np.float32))
        box = cv2.boxPoints(bbox)
        center = np.mean(box, axis=0)
        width, height = bbox[1]
        angle = bbox[2]

        if width <= 0 or height <= 0:
            raise ValueError("Invalid bounding box dimensions.")

    except cv2.error as e:
        print(f"OpenCV error in minAreaRect: {e}")
        print(f"Points shape: {points.shape}, dtype: {points.dtype}")
        print(f"Points sample: {points[:3] if len(points) >= 3 else points}")
        raise ValueError(f"Failed to compute minimum area rectangle: {e}")

    zigzag_coords = []

    # Determine which dimension is shorter for better zigzag efficiency
    if width < height:
        # Width is shorter - generate lines along width direction
        shorter_dim = width
        longer_dim = height
        # Generate points along x-axis (width)
        direction = 1
        num_lines = max(1, int(shorter_dim // spacing))
        for i in range(num_lines):
            x_offset = (i * spacing) - (shorter_dim / 2)
            x_new = center[0] + x_offset
            y_top = center[1] - (longer_dim / 2)
            y_bottom = center[1] + (longer_dim / 2)

            if direction == 1:
                zigzag_coords.extend([(x_new, y_top), (x_new, y_bottom)])
            else:
                zigzag_coords.extend([(x_new, y_bottom), (x_new, y_top)])
            direction *= -1
    else:
        # Height is shorter - generate lines along height direction
        shorter_dim = height
        longer_dim = width
        # Generate points along y-axis (height)
        direction = 1
        num_lines = max(1, int(shorter_dim // spacing))
        for i in range(num_lines):
            y_offset = (i * spacing) - (shorter_dim / 2)
            y_new = center[1] + y_offset
            x_left = center[0] - (longer_dim / 2)
            x_right = center[0] + (longer_dim / 2)

            if direction == 1:
                zigzag_coords.extend([(x_left, y_new), (x_right, y_new)])
            else:
                zigzag_coords.extend([(x_right, y_new), (x_left, y_new)])
            direction *= -1

    if not zigzag_coords:
        # Fallback: return original contour if zigzag generation fails
        print("Warning: No zigzag points generated, returning original contour")
        return points.reshape(-1, 1, 2).astype(np.float32)

    # Apply rotation if the bounding box is rotated
    if abs(angle) > 0.1:  # Only rotate if angle is significant
        # Convert points to homogeneous coordinates for rotation
        zigzag_array = np.array(zigzag_coords, dtype=np.float32)
        ones = np.ones((zigzag_array.shape[0], 1))
        points_homogeneous = np.hstack([zigzag_array, ones])

        # Compute rotation matrix
        theta = np.radians(angle)
        cos_theta = np.cos(theta)
        sin_theta = np.sin(theta)

        rotation_matrix = np.array([
            [cos_theta, -sin_theta, center[0] - center[0] * cos_theta + center[1] * sin_theta],
            [sin_theta, cos_theta, center[1] - center[0] * sin_theta - center[1] * cos_theta],
            [0, 0, 1]
        ])

        # Apply rotation transformation
        rotated_points = (rotation_matrix @ points_homogeneous.T).T[:, :2]

        return rotated_points.reshape(-1, 1, 2).astype(np.float32)
    else:
        # No significant rotation needed
        return np.array(zigzag_coords, dtype=np.float32).reshape(-1, 1, 2)
