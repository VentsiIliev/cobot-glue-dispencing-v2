import cv2
import numpy as np
from matplotlib import pyplot as plt

from src.plvision.PLVision import Contouring
# from matplotlib import pyplot as plt

import numpy as np


def transformSinglePointToCamera(robot_point, cameraToRobotMatrix):
    """
    Transforms a single robot point to camera coordinates using a homography.

    Parameters:
        robot_point: tuple or list (x, y)
        cameraToRobotMatrix: 3x3 homography matrix mapping camera -> robot

    Returns:
        (x_cam, y_cam): transformed camera point
    """
    # Invert the camera-to-robot homography
    robotToCameraMatrix = np.linalg.inv(cameraToRobotMatrix)

    # Convert to homogeneous coordinates
    homogeneous_point = np.array([robot_point[0], robot_point[1], 1])

    # Apply transformation
    transformed_hom = robotToCameraMatrix @ homogeneous_point

    # Normalize to Cartesian coordinates
    x_cam = transformed_hom[0] / transformed_hom[2]
    y_cam = transformed_hom[1] / transformed_hom[2]

    return x_cam, y_cam

def transformToCameraPoints(robot_contour, cameraToRobotMatrix):
    # Invert the camera-to-robot transformation matrix
    robotToCameraMatrix = np.linalg.inv(cameraToRobotMatrix)

    transformed_points = []

    # Flatten the contour if it is in the form (num_points, 1, 2)
    if len(robot_contour.shape) == 3 and robot_contour.shape[1] == 1 and robot_contour.shape[2] == 2:
        robot_contour = robot_contour.reshape(-1, 2)  # Flatten the contour

    for point in robot_contour:
        # Ensure each point is in the form (x, y)
        if len(point) != 2:
            raise ValueError(f"Contour point has an unexpected shape: {point}")

        # Convert point to homogeneous coordinates (x, y, 1)
        homogeneous_point = np.array([point[0], point[1], 1])

        # Apply the inverse transformation matrix (robotToCameraMatrix)
        transformed_point = np.dot(robotToCameraMatrix, homogeneous_point)

        # Convert back to non-homogeneous coordinates (x / z, y / z)
        transformed_points.append(
            (transformed_point[0] / transformed_point[2], transformed_point[1] / transformed_point[2]))

    return transformed_points


def interpolate_contour(contour, num_points):
    """
    Interpolates a contour by adding intermediate points between consecutive points.
    """
    new_contour = []
    for i in range(len(contour)):
        pt1 = contour[i]
        pt2 = contour[(i + 1) % len(contour)]  # wrap around to the first point
        for t in np.linspace(0, 1, num_points):  # Interpolation factor
            new_contour.append([
                int(pt1[0] + t * (pt2[0] - pt1[0])),
                int(pt1[1] + t * (pt2[1] - pt1[1]))
            ])
    return np.array(new_contour)


def get_orientation(contour):
    """
    Compute the orientation of the object using image moments.

    This function calculates the orientation angle of a given contour using the image moments.
    The orientation is determined by the angle of the major axis of the ellipse that has the same
    second-moments as the region. The angle is computed in degrees.

    Parameters:
    ----------
    contour : np.ndarray
        A 2D array of shape (N, 1, 2), where N is the number of points in the contour.
        Each point is represented as [[x, y]].

    Returns:
    -------
    float
        The orientation angle of the contour in degrees. The angle is measured counterclockwise
        from the positive x-axis. If the contour has zero variance in the x-direction (mu20 is zero),
        the function returns 0 to avoid division by zero.

    Notes:
    -----
    - The function uses the image moments to calculate the orientation. The moments are statistical
      properties of the contour that provide information about its shape.
    - The angle is calculated using the arctangent function (`np.arctan2`) and converted from radians
      to degrees.
    - The function handles the case where the second central moment in the x-direction (mu20) is zero
      to avoid division by zero.

    Dependencies:
    ------------
    - `cv2.moments`: A function from the OpenCV library to compute the image moments of the contour.
    - `np.arctan2`: A function from the NumPy library to compute the arctangent of the quotient of its arguments.
    - `np.degrees`: A function from the NumPy library to convert an angle from radians to degrees.
    """
    moments = cv2.moments(np.array(contour, dtype=np.float32))

    if moments["mu20"] == 0:  # Avoid division by zero
        return 0

    angle = 0.5 * np.arctan2(2 * moments["mu11"], moments["mu20"] - moments["mu02"])

    # Convert radians to degrees
    return np.degrees(angle)


def applyTransformation(cameraToRobotMatrix, contours):
    """
    Applies a perspective transformation to a list of contours using a provided camera-to-robot transformation matrix.

    This function takes in a camera-to-robot transformation matrix and a list of contours (each contour being a list of points),
    applies the transformation matrix to each contour, and returns the transformed contours. The transformation is done using
    the OpenCV function `cv2.perspectiveTransform`, which performs a matrix transformation to map 2D points from one plane to another.

    Args:
        cameraToRobotMatrix (numpy.ndarray): A 3x3 matrix representing the transformation from the camera's coordinate system
                                              to the robot's coordinate system. This matrix should be of type `float32`.
        contours (list): A list of contours, where each contour is a list of points (2D coordinates) in the form of tuples or lists.
                         The points within each contour should be in the form (x, y).

    Returns:
        list: A list of transformed contours, where each contour is a list of transformed points. Each transformed point is
              represented as a tuple (x, y) with 6 decimal places precision.

    Example:
        cameraToRobotMatrix = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]], dtype=np.float32)
        contours = [[(0, 0), (1, 0), (1, 1), (0, 1)], [(2, 2), (3, 2), (3, 3), (2, 3)]]
        transformed_contours = applyTransformation(cameraToRobotMatrix, contours)
        print(transformed_contours)

    Notes:
        - The input `contours` should be a list where each contour is a list of points in the format [(x1, y1), (x2, y2), ...].
        - The transformation matrix `cameraToRobotMatrix` is assumed to be a valid 3x3 matrix for perspective transformation.
        - The function rounds the output points to 6 decimal places for precision control.
    """
    transformedContours = []

    for contour in contours:
        # Convert contour to a numpy array and reshape it for perspective transformation
        contour = np.array(contour, dtype=np.float32).reshape(-1, 1, 2)

        # Apply perspective transformation using the camera-to-robot matrix
        transformed_points = cv2.perspectiveTransform(contour, cameraToRobotMatrix)

        # Round the transformed points to 6 decimal places and reshape back to the appropriate format
        # transformed_points = np.round(transformed_points, decimals=6).reshape(-1, 2)  # Flatten the output
        transformed_points = np.round(transformed_points, decimals=6)  # Flatten the output

        # Append the transformed points as a list of tuples
        transformedContours.append(transformed_points.tolist())

    return transformedContours


def shrinkContour(contourParam, offset_x, offset_y):
    """
    Shrinks a contour inward by exactly the specified offsets for X and Y directions towards the centroid.

    :param contourParam: np.array of shape (N, 2) representing the contour in mm.
    :param offset_x: The shrink amount in millimeters for the X direction.
    :param offset_y: The shrink amount in millimeters for the Y direction.
    :return: np.array of the shrunken contour with the same format.
    """

    contour = np.array(contourParam, dtype=np.float32).reshape(-1, 2)
    # Calculate the centroid of the contour
    if len(contour) == 0 or len(contour[0]) != 2:
        raise ValueError("Contour must be a list of tuples or a NumPy array with shape (n, 2)")

    centroid = Contouring.calculateCentroid(contour)

    # Create a new array for the shrunken contour
    shrunk_contour = np.zeros_like(contour)

    for i, (x, y) in enumerate(contour):
        # Calculate the direction vector from the point to the centroid
        direction = np.array([centroid[0] - x, centroid[1] - y])

        # Normalize the direction vector
        norm = np.linalg.norm(direction)
        if norm == 0:  # Avoid division by zero for degenerate cases
            shrunk_contour[i] = [x, y]
            continue
        direction /= norm

        # Shrink the point by exactly the specified offsets along X and Y axes
        shrunk_contour[i] = np.array([x + direction[0] * offset_x,
                                      y + direction[1] * offset_y])

    return shrunk_contour.astype(np.float32)


def shrinkContours(contours, offset_x, offset_y):
    """
    Shrinks a list of contours inward by exactly the specified offsets for X and Y directions towards the centroid.

    :param contours: A list of contours, where each contour is a list of points (2D coordinates) in the form of tuples or lists.
    :param offset_x: The shrink amount in millimeters for the X direction.
    :param offset_y: The shrink amount in millimeters for the Y direction.
    :return: A list of shrunken contours, where each contour is a list of shrunken points.
    """

    shrunkContours = []
    for cnt in contours:
        shrunkContour = shrinkContour(cnt, offset_x, offset_y)
        shrunkContours.append(shrunkContour)

    return shrunkContours


def offset_point(point, offsetX, offsetY):
    """
    Offsets a point by a given offset.

    :param zOffset:
    :param point: The point to offset (x, y).
    :param offsetX: The offset to apply to the point x coordinate.
    :param offsetY: The offset to apply to the point y coordinate.
    :return: The offset point (x', y').
    """
    return [point[0][0] + offsetX, point[0][1] + offsetY]


def rotate_point(point, angle, pivot):
    """
    Rotates a point around a given origin by a given angle.

    :param point: The point to rotate (x, y).
    :param angle: The angle to rotate the point (in degrees).
    :param pivot: The pivot to rotate around (x, y).
    :return: The rotated point (x', y').
    """
    angle_rad = np.radians(angle)
    print("Pivot ",pivot)
    pivotX = pivot[0]
    pivotY = pivot[1]

    pointX = point[0]
    pointY = point[1]

    rotatedX = pivotX + np.cos(angle_rad) * (pointX - pivotX) - np.sin(angle_rad) * (pointY - pivotY)
    rotatedY = pivotY + np.sin(angle_rad) * (pointX - pivotX) + np.cos(angle_rad) * (pointY - pivotY)

    return [rotatedX, rotatedY]

def rotateContour(contour, angle, pivot):
    """
    Rotates a contour around a given origin by a given angle.

    :param contour: The contour to rotate.
    :param angle: The angle to rotate the contour (in degrees).
    :param pivot: The pivot to rotate around (x, y).
    :return: The rotated contour.
    """
    rotatedContour = []
    for point in contour:
        point = point[0]
        rotatedPoint = rotate_point(point, angle, pivot)
        rotatedContour.append([rotatedPoint])
    return rotatedContour


def convertContourToMillimeters(points, ppmX, ppmY):
    """
        Convert the contour coordinates from pixels to millimeters.

        :param points: The contour points in pixels.
        :param ppmX: Pixels per millimeter in the x direction.
        :param ppmY: Pixels per millimeter in the y direction.
        :return: The contour points in millimeters.
        """
    pointsInMillimeters = []
    for point in points:
        point = [point[0][0] / ppmX, point[0][1] / ppmY]
        pointsInMillimeters.append(point)
    return pointsInMillimeters


def calculateAngleRelativeToY(currentPoint, nextPoint):
    """
    Calculate the angle relative to the Y-axis and the distance between two points.

    :param currentPoint: The current point (x, y).
    :param nextPoint: The next point (x, y).
    :return: A tuple containing the angle relative to the Y-axis (in degrees) and the distance between the points.
    """
    deltaX = nextPoint[0] - currentPoint[0]
    deltaY = nextPoint[1] - currentPoint[1]
    rLength = np.sqrt(deltaX ** 2 + deltaY ** 2)
    # print(f"    deltaX: {deltaX}, deltaY: {deltaY}, rLength: {rLength}")
    rWork = deltaY / rLength
    rAngleY = np.arccos(rWork)
    # convert to degrees
    rAngleY = np.degrees(rAngleY)
    return rAngleY, rLength


def calculateAngleRelativeToX(currentPoint, nextPoint):
    """
    Calculate the angle relative to the X-axis and the distance between two points.

    :param currentPoint: The current point (x, y).
    :param nextPoint: The next point (x, y).
    :return: A tuple containing the angle relative to the X-axis (in degrees) and the distance between the points.
    """
    deltaX = nextPoint[0] - currentPoint[0]
    deltaY = nextPoint[1] - currentPoint[1]
    rLength = np.sqrt(deltaX ** 2 + deltaY ** 2)
    rWork = deltaX / rLength
    rAngleX = np.arccos(rWork)
    rAngleX = np.degrees(rAngleX)
    return rAngleX, rLength





def translateContour(contour, offsetX=0, offsetY=0):
    """
    Translates a contour by a given offset.

    :param contour: The contour to translate.
    :param offsetX: The offset to apply to the contour x coordinates.
    :param offsetY: The offset to apply to the contour y coordinates.
    :return: The translated contour.
    """
    translatedContour = []
    for point in contour:
        translatedPoint = offset_point(point, offsetX, offsetY)
        translatedContour.append(translatedPoint)

    return translatedContour


def reorderContourPointsHighestYValue(contour):
    yTarget = -100000
    index = -1

    # find the highest Y
    for i in range(len(contour) - 1):
        y = contour[i][0][1]
        if y > yTarget:
            yTarget = y
            index = i

    # Reorder the contour to start from the point with the highest y and lowest x value
    reordered_contour = np.concatenate((contour[index:], contour[:index]), axis=0)
    return reordered_contour


def reorderContourPointsLowestYValue(contour):
    yTarget = 100000  # Initialize to a very high value
    index = -1

    # find the lowest Y
    for i in range(len(contour) - 1):
        y = contour[i][0][1]
        if y < yTarget:
            yTarget = y
            index = i

    # Reorder the contour to start from the point with the lowest y and lowest x value
    reordered_contour = np.concatenate((contour[index:], contour[:index]), axis=0)
    return reordered_contour


def compute_motion_params(length, base_vel=50, k_v=0.2, base_acc=100, k_a=0.1, max_blendR=2):
    """
    Compute dynamic velocity, acceleration, and blending radius for a motion segment
    based on its length.

    This function adjusts the velocity, acceleration, and blending radius of a motion
    segment dynamically using a linear relationship with the segment's length. These
    parameters are commonly used in motion planning, such as in robotics or animation.

    Parameters:
    ----------
    length : float
        The length of the motion segment. Must be a non-negative value.
    base_vel : float, optional
        The base velocity to use when the segment length is zero. Default is 50.
    k_v : float, optional
        The proportional factor for velocity adjustment based on length. Default is 0.2.
    base_acc : float, optional
        The base acceleration to use when the segment length is zero. Default is 100.
    k_a : float, optional
        The proportional factor for acceleration adjustment based on length. Default is 0.1.
    max_blendR : float, optional
        The maximum allowable blending radius. Default is 2.

    Returns:
    -------
    tuple
        A tuple containing:
        - vel (float): The computed velocity for the motion segment.
        - acc (float): The computed acceleration for the motion segment.
        - blendR (float): The computed blending radius for the motion segment.

    Examples:
    --------
    >>> compute_motion_params(10)
    (52.0, 101.0, 1.0)

    >>> compute_motion_params(25, base_vel=60, k_v=0.5, base_acc=150, k_a=0.3, max_blendR=5)
    (72.5, 157.5, 2.5)

    Notes:
    -----
    - The velocity (`vel`) is calculated as:
        `vel = base_vel + length * k_v`
      where `base_vel` is the base velocity, and `k_v` is the velocity proportionality constant.
    - The acceleration (`acc`) is calculated as:
        `acc = base_acc + length * k_a`
      where `base_acc` is the base acceleration, and `k_a` is the acceleration proportionality constant.
    - The blending radius (`blendR`) is limited by `max_blendR` to prevent overly large values:
        `blendR = min(length * 0.10, max_blendR)`
    - Ensure that the `length` is non-negative to avoid unexpected results.

    """
    vel = base_vel + length * k_v  # Adjust velocity based on length
    acc = base_acc + length * k_a  # Adjust acceleration based on length
    blendR = min(length * 0.10, max_blendR)  # Blending radius proportional to length
    return vel, acc, blendR


def plotPoints(points):
    """
    Plots the given points using matplotlib.

    :param points: The points to plot.
    """
    x_coords = [point[0] for point in points]  # Extract the x coordinates from the points
    y_coords = [point[1] for point in points]  # Extract the y coordinates from the points
    plt.figure()  # Create a new figure
    plt.plot(x_coords, y_coords, 'bo')  # Plot the points with blue circle markers
    plt.xlabel('X')  # Set the x-axis label
    plt.ylabel('Y')  # Set the y-axis label
    plt.title('Contour Points')  # Set the title of the plot
    plt.axis('equal')  # Set equal scaling for both axes
    plt.show()  # Display the plot


def saveContour(contour, fileName):
    """
    Saves the given contour to a file.

    :param contour: The contour to save.
    """
    with open(fileName, 'w') as file:  # Open a file for writing
        for point in contour:  # Iterate through each point in the contour
            file.write(f'{point[0]},{point[1]}\n')  # Write the point to the file
    print('Contour saved to contourCircle.txt')  # Print a message indicating that the contour has been saved


def translatePointToRobotCoordinates(point):
    """
       Translates a point from image coordinates (in pixels) to robot coordinates (in millimeters).

       This function is responsible for converting a 2D point represented in image coordinates
       (x, y), where (0, 0) corresponds to the top-left corner of the image, into the corresponding
       point in the robot's coordinate system. The transformation assumes a known offset between
       the image origin and the robot's origin, which is provided as a fixed offset in millimeters.

       The image coordinates are typically in pixels, with the origin at the top-left corner.
       The robot coordinates, on the other hand, are in millimeters and are relative to the
       robot's reference frame, where the robot's origin is located at a specific point in the
       robot's workspace.

       The translation applies the following assumptions:
       - The point in image coordinates is provided in millimeters, so no conversion from pixels to
         millimeters is performed.
       - The `imageOriginInRobotCoords` represents the known distance from the robot's origin
         to the image's origin (the top-left corner of the camera view) in the robot's coordinate
         system.

       Parameters:
       ----------
       point : list of two floats
           A list representing the point in image coordinates (x, y), where both `x` and `y`
           are given in millimeters.

       Returns:
       -------
       list of two floats
           The translated point in robot coordinates (x', y'). The values are given in millimeters.

       Example:
       --------
       image_point = [100, 150]  # Example image coordinates (in millimeters)
       robot_point = translatePointToRobotCoordinates(image_point)
       print(robot_point)  # Output: [358, 93] (robot coordinates in millimeters)

       Notes:
       -----
       - The translation is based on a fixed offset (258, 243) for the origin of the image and
         the robot, which should be adjusted if the camera's relative position to the robot changes.
       - This function is essential for converting points detected by the camera system into a
         coordinate system that the robot can understand and act upon.
       """
    imageOriginInRobotCoords = [258, 243]  # x y distance from robot origin to image origin in millimeters
    pointX = point[0]
    pointY = point[1]
    newPointX = imageOriginInRobotCoords[0] + pointX
    newPointY = imageOriginInRobotCoords[1] - pointY
    return [newPointX, newPointY]


def angleRelativeToX(point, center):
    """
    Calculate the angle of a point relative to the centroid, using the X-axis as the reference.

    The angle is measured counterclockwise from the positive X-axis to the line segment
    connecting the centroid and the point. The result is in radians, with a range of [-π, π].

    This function is commonly used for:
    - Reordering points in a circular manner (e.g., clockwise or counterclockwise).
    - Determining the relative position of a point in polar coordinates.

    Parameters:
    ----------
    point : tuple
        A tuple (x, y) representing the coordinates of the point for which to calculate the angle.
    center : tuple
        A tuple (cx, cy) representing the coordinates of the centroid (or reference point).

    Returns:
    -------
    float
        The angle in radians, ranging from -π to π. A positive value indicates a counterclockwise
        angle from the X-axis, while a negative value indicates a clockwise angle.

    Examples:
    --------
    >>> angleRelativeToX((5, 7), (3, 4))
    0.982793723247329

    >>> angleRelativeToX((3, 4), (3, 4))
    0.0  # No angle when point coincides with the centroid

    Notes:
    -----
    - This function uses the arctangent function (`np.arctan2`) to compute the angle, which handles
      all quadrants correctly.
    - The function assumes a Cartesian coordinate system where the origin is at the bottom-left.

    """
    return np.arctan2(point[1] - center[1], point[0] - center[0])


def reorderContourByAngle(contour):
    """
    Reorders the points of a contour in a clockwise or counterclockwise order
    based on their angle relative to the centroid of the shape.

    The function calculates the centroid of the given contour and computes the angle
    of each point relative to the X-axis passing through the centroid. The points are
    then sorted based on these angles to determine their order.

    Parameters:
    ----------
    contour : np.ndarray
        A 2D array of shape (N, 1, 2), where N is the number of points in the contour.
        Each point is represented as [[x, y]].

    Returns:
    -------
    np.ndarray
        A 2D array of shape (N, 2), containing the reordered points of the contour.
        Each point is represented as [x, y].

    Steps:
    -----
    1. Calculate the centroid of the contour using the moments.
    2. Compute the angle of each point relative to the centroid using the X-axis as a reference.
    3. Sort the points by their angle in ascending order to achieve counterclockwise sorting.
    4. Return the reordered points as a NumPy array.

    Examples:
    --------
    >>> contourExample = np.array([[[1, 2]], [[3, 4]], [[5, 0]]])
    >>> reorderContourByAngle(contourExample)
    array([[5, 0],
           [3, 4],
           [1, 2]])

    Notes:
    -----
    - The angles are computed using the `angleRelativeToX` function, which measures
      angles relative to the X-axis.
    - Sorting counterclockwise is achieved by sorting the angles in ascending order.
    - If a clockwise order is required, simply sort the angles in descending order.

    Dependencies:
    ------------
    - `Contouring.calculateCentroid`: A function to compute the centroid of a set of points.
    - `angleRelativeToX`: A function to calculate the angle relative to the centroid.

    """
    # Calculate the centroid of the contour (center of mass)
    center = Contouring.calculateCentroid(np.array(contour))

    # Calculate the angle of each point relative to the centroid
    angles = []
    for point in contour:
        x, y = point[0]
        angle = angleRelativeToX((x, y), center)  # Angle with respect to the centroid
        angles.append((angle, (x, y)))  # Store angle and point

    # Sort the points based on the angle (counterclockwise)
    sortedPoints = [point for _, point in sorted(angles, key=lambda a: a[0])]

    # Return the reordered contour
    return np.array(sortedPoints)


def scaleContour(contour, scaleFactor):
    if contour is None or len(contour) == 0:
        raise ValueError("Contour is empty or None")

    # Scale each point in the contour by the scaling factor
    scaledContour = []
    for point in contour:
        x, y = point[0]  # Extract x, y coordinates (no need for point[0])
        scaled_x = x * scaleFactor
        scaled_y = y * scaleFactor
        scaledContour.append([scaled_x, scaled_y])

    # Convert scaled_contour back to the appropriate format (numpy array)
    scaledContour = np.array(scaledContour, dtype=np.int32)
    return scaledContour




