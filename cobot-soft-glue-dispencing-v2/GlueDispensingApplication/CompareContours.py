import os

import cv2
import numpy as np
import copy
import traceback
from API.shared.Contour import Contour

SIMILARITY_THRESHOLD = 70
DEFECT_THRESHOLD = 5


# def _isValid(contour):
#     """Check if the contour is valid."""
#     return contour is not None and len(contour) > 0

def _isValid(sprayPatternList):
    """
  Check if the given spray pattern list is valid.

  Args:
      sprayPatternList (list): A list of spray pattern contours to be validated.

  Returns:
      bool: True if the spray pattern list is not empty and not None, False otherwise.
  """

    return sprayPatternList is not None and len(sprayPatternList) > 0


def findMatchingWorkpieces(workpieces, newContours):
    """
        Find matching workpieces based on new contours and align them.

        This function compares the contours of workpieces with the new contours and aligns them
        based on the similarity and defect thresholds.

        Args:
            workpieces (list): List of workpieces to compare against.
            newContours (list): List of new contours to be matched.

        Returns:
            tuple: A tuple containing:
                - finalMatches (list): List of workpieces that have been aligned and matched.
                - noMatches (list): List of contours that couldn't be matched.
                - newContoursWithMatches (list): List of new contours that have been matched.
        """
    # print(f"in findMatchingWorkpieces")
    """FIND MATCHES BETWEEN NEW CONTOURS AND WORKPIECES."""
    matched, noMatches, newContoursWithMatches = _findMatches(newContours, workpieces)

    """ALIGN MATCHED CONTOURS."""
    finalMatches = _alignContours(matched, defectsThresh=DEFECT_THRESHOLD)

    # print(f"Final Matched {len(finalMatches)} workpieces")
    return finalMatches, noMatches, newContoursWithMatches
    # return matched, noMatches, newContoursWithMatches


def _remove_contour(newContours, contour_to_remove):
    """
   Safely remove an exact matching contour from the newContours list.

   Args:
       newContours (list): List of contours from which the matching contour should be removed.
       contour_to_remove (array): The contour to be removed.

   Returns:
       None
   """

    for i, stored_contour in enumerate(newContours):
        if np.array_equal(stored_contour, contour_to_remove):
            del newContours[i]  # Remove the matching contour
            return
    print(f"Error: Could not find an exact match to remove.")


def _findMatches(newContours, workpieces):
    """
       Find matches between new contours and workpieces based on similarity.

       This function compares each new contour with all the workpieces and determines the best
       match based on similarity and centroid/rotation differences.

       Args:
           newContours (list): List of new contours to be compared.
           workpieces (list): List of workpieces containing contour data to match against.

       Returns:
           tuple: A tuple containing:
               - matched (list): A list of matched workpieces along with the corresponding data.
               - noMatches (list): A list of contours that couldn't be matched.
               - newContourWithMatches (list): A list of new contours that were matched.
       """
    print(f"Finding matches ")
    matched = []  # List of matched workpieces
    noMatches = []  # List of contours that did not match
    newContourWithMatches = []
    centroidDiffList, rotationDiffList = [], []  # Store differences

    #create white canvas image

    count = 0

    for contour in newContours.copy():
        canvas = np.ones((720, 1280, 3), dtype=np.uint8) * 255
        contour = Contour(contour)  # Convert to Contour object to use the methods
        contour.draw(canvas, color=(0, 0, 255), thickness=2)  # Draw the contour on the canvas
        best_match = None
        best_similarity = -1  # Start with the lowest similarity
        best_centroid_diff = None
        best_rotation_diff = None
        for workpiece in workpieces:
            print("     comparing: ", workpiece.workpieceId)
            workpieceContour = Contour(workpiece.contour.get("contour"))  # Convert to Contour object to use the methods
            if workpieceContour is None:
                print(f"    Workpiece contour is None")
                continue
            workpieceContour.draw(canvas, color=(0, 255, 0), thickness=2)  # Draw the contour on the canvas
            cv2.imwrite("findMatches_" + str(count) + ".png", canvas)
            count += 1
            similarity = _getSimilarity(workpieceContour.get_contour_points(), contour.get_contour_points())
            print(f"    Similarity: {similarity}")

            if similarity > SIMILARITY_THRESHOLD and similarity > best_similarity:
                best_match = workpiece
                # best_match.contour = contour.get_contour_points()
                best_similarity = similarity
                best_centroid_diff, best_rotation_diff, contourAngle = _calculateDifferences(workpieceContour, contour)
                # print(f"    Diff: {best_centroid_diff}, {best_rotation_diff}")

        if best_match is not None:
            # Store the best match for this contour
            # print(f"    Best Match Found - Similarity: {best_similarity}")

            # Append results
            newContourWithMatches.append(contour.get_contour_points())

            matchDict = {"workpieces": best_match,
                         "newContour": contour.get_contour_points(),
                         "centroidDiff": best_centroid_diff,
                         "rotationDiff": best_rotation_diff,
                         "contourOrientation": contourAngle}

            # print the formated matchDicts
            print(f"    in _findMatcher: {best_match.get_spray_pattern_contours()}")

            # matched.append(best_match)
            matched.append(matchDict)
            _remove_contour(newContours, contour.get_contour_points())
        else:
            print(f"    No match found for this contour")
    noMatches = newContours  # Remaining unmatched contours

    return matched, noMatches, newContourWithMatches


def _alignContours(matched, defectsThresh=5):
    """
    Align matched contours to the workpieces by rotating and translating based on differences.

    Args:
        matched (list): List of matched workpieces and their corresponding contour differences.
        defectsThresh (float): Threshold for comparing convexity defects.

    Returns:
        list: List of workpieces with aligned contours.
    """
    transformedMatchesDict = {"workpieces": [], "orientations": []}

    for i, match in enumerate(matched):
        workpiece = copy.deepcopy(match["workpieces"])
        newContour = match["newContour"]
        rotationDiff = match["rotationDiff"]
        centroidDiff = match["centroidDiff"]
        contourOrientation = match["contourOrientation"]

        canvas = np.ones((720, 1280, 3), dtype=np.uint8) * 255

        newCntObject = Contour(newContour)
        newCntObject.draw(canvas, color=(255, 255, 0), thickness=2)  # Draw the new contour
        if not _isValid(workpiece.contour.get("contour")):
            raise ValueError("invalid contour")
            continue

        # ✅ Prepare main contour object
        contourObj = Contour(workpiece.contour.get("contour"))
        # ✅ Use the helper methods to get spray pattern data correctly
        sprayContourEntries = workpiece.get_spray_pattern_contours()
        sprayFillEntries = workpiece.get_spray_pattern_fills()

        # print("_alignContours sprayContourEntries: ", len(sprayContourEntries))
        # print("_alignContours sprayFillEntries: ", len(sprayFillEntries))

        # ✅ Create Contour objects for each spray pattern entry
        sprayContourObjs = []
        for entry in sprayContourEntries:
            contour_data = entry.get("contour")
            if contour_data is not None and len(contour_data) > 0:
                obj = Contour(contour_data)
                sprayContourObjs.append(obj)
                # print(f"    Spray Contour OBJ: {obj.get_contour_points()}")

        sprayFillObjs = []
        for entry in sprayFillEntries:
            contour_data = entry.get("contour")
            if contour_data is not None and len(contour_data) > 0:
                sprayFillObjs.append(Contour(contour_data))

        contourObj.draw(canvas, color=(0, 0, 255), thickness=2)  # Draw the main contour

        # ✅ Apply transformations
        centroid = contourObj.getCentroid()

        # Rotation
        print(f"    Applying rotation: {rotationDiff} degrees around Pivot {centroid} to External Contour")
        contourObj.rotate(rotationDiff, centroid)
        contourObj.draw(canvas, color=(0, 255, 0), thickness=2)  # Draw the rotated contour

        print(f"    Applying rotation: {rotationDiff} degrees around Pivot {centroid} to Spray contour")
        for obj in sprayContourObjs:
            obj.rotate(rotationDiff, centroid)

        print(f"    Applying rotation: {rotationDiff} degrees around Pivot {centroid} to Fill contour")
        for obj in sprayFillObjs:
            obj.rotate(rotationDiff, centroid)

        # Translation
        contourObj.translate(*centroidDiff)
        contourObj.draw(canvas, color=(255, 0, 0), thickness=2)  # Draw the translated contour
        cv2.imwrite("aligned_contour_" + str(i) + ".png", canvas)
        for obj in sprayContourObjs:
            obj.translate(*centroidDiff)
        for obj in sprayFillObjs:
            obj.translate(*centroidDiff)

        # ✅ Update the workpiece with transformed contours
        workpiece.contour = {"contour": contourObj.get_contour_points(), "settings": {}}

        # ✅ Update spray pattern contours correctly
        if sprayContourObjs and "Contour" in workpiece.sprayPattern:
            for i, obj in enumerate(sprayContourObjs):
                if i < len(workpiece.sprayPattern["Contour"]):
                    workpiece.sprayPattern["Contour"][i]["contour"] = obj.get_contour_points()

        if sprayFillObjs and "Fill" in workpiece.sprayPattern:
            for i, obj in enumerate(sprayFillObjs):
                if i < len(workpiece.sprayPattern["Fill"]):
                    workpiece.sprayPattern["Fill"][i]["contour"] = obj.get_contour_points()

        # Compare contours
        print(f"SKIP: _compareContoursHullAndDefects FOR DEBUGGING")

        # _compareContoursHullAndDefects(defectsThresh, newContour, workpiece)

        transformedMatchesDict["workpieces"].append(workpiece)
        transformedMatchesDict["orientations"].append(contourOrientation)
        external = workpiece.contour.get("contour")
        # print(f"    Transformed Match {i + 1}: {external}")
    return transformedMatchesDict


def _compareContoursHullAndDefects(defectsThresh, newContours, workpieceCopy):
    """
    Compare the convexity defects and hulls between the new contour and workpiece contour.

    Args:
        defectsThresh (float): Threshold for defect comparison.
        newContours (list): List of new contours to be compared.
        workpieceCopy (Workpiece): A workpiece object to compare against.

    Returns:
        None
    """

    # ✅ Handle the main contour correctly
    if isinstance(workpieceCopy.contour, dict) and "contour" in workpieceCopy.contour:
        workpieceCopyContourObject = Contour(workpieceCopy.contour["contour"])
    else:
        # Fallback for direct contour data
        workpieceCopyContourObject = Contour(workpieceCopy.contour)

    newContourObject = Contour(newContours)

    # Get convexity defects
    hull = workpieceCopyContourObject.getConvexHull()
    hull2 = newContourObject.getConvexHull()
    ret, workpieceDefects = workpieceCopyContourObject.getConvexityDefects()
    ret, newDefects = newContourObject.getConvexityDefects()

    if workpieceDefects is None or newDefects is None:
        print("No defects found in workpiece contour")
        return

    workpieceLargestDefect = _getLargestDefect(workpieceDefects, workpieceCopyContourObject.get_contour_points())
    newContourLargestDefect = _getLargestDefect(newDefects, newContourObject.get_contour_points())

    if workpieceLargestDefect is None or newContourLargestDefect is None:
        print("No defects found in new contour")
        return

    # Calculate distance between largest defects
    distance = np.linalg.norm(np.array(workpieceLargestDefect) - np.array(newContourLargestDefect))

    # Rotate 180 degrees if distance is greater than threshold
    if distance > defectsThresh:
        newCentroid = workpieceCopyContourObject.getCentroid()
        workpieceCopyContourObject.rotate(180, newCentroid)

        # ✅ Update main contour
        if isinstance(workpieceCopy.contour, dict):
            workpieceCopy.contour["contour"] = workpieceCopyContourObject.get_contour_points()
        else:
            workpieceCopy.contour = workpieceCopyContourObject.get_contour_points()

        # ✅ Update spray pattern if it exists
        if _isValid(workpieceCopy.sprayPattern):
            # Use helper methods to get spray pattern data
            sprayContourEntries = workpieceCopy.get_spray_pattern_contours()
            sprayFillEntries = workpieceCopy.get_spray_pattern_fills()

            # Rotate spray contours
            sprayContourObjs = []
            for entry in sprayContourEntries:
                contour_data = entry.get("contour")
                if contour_data is not None and len(contour_data) > 0:
                    obj = Contour(contour_data)
                    obj.rotate(180, newCentroid)
                    sprayContourObjs.append(obj)

            # Rotate spray fills
            sprayFillObjs = []
            for entry in sprayFillEntries:
                contour_data = entry.get("contour")
                if contour_data is not None and len(contour_data) > 0:
                    obj = Contour(contour_data)
                    obj.rotate(180, newCentroid)
                    sprayFillObjs.append(obj)

            # ✅ Update the spray pattern with rotated contours
            if sprayContourObjs and "Contour" in workpieceCopy.sprayPattern:
                for i, obj in enumerate(sprayContourObjs):
                    if i < len(workpieceCopy.sprayPattern["Contour"]):
                        workpieceCopy.sprayPattern["Contour"][i]["contour"] = obj.get_contour_points()

            if sprayFillObjs and "Fill" in workpieceCopy.sprayPattern:
                for i, obj in enumerate(sprayFillObjs):
                    if i < len(workpieceCopy.sprayPattern["Fill"]):
                        workpieceCopy.sprayPattern["Fill"][i]["contour"] = obj.get_contour_points()


def _getLargestDefect(defects, contour):
    """
        Get the largest defect from a list of convexity defects.

        Args:
            defects (list): List of convexity defects.
            contour (list): List of contour points used for defect calculation.

        Returns:
            tuple: Coordinates of the farthest defect point.
        """
    largest_defect = max(defects, key=lambda x: x[0][3])
    s, e, f, d = largest_defect[0]  # s = start, e = end, f = far, d = distance
    start = tuple(contour[s][0])
    end = tuple(contour[e][0])
    far = tuple(contour[f][0])
    return far


def _calculateDifferences(workpieceContour, contour):
    """
       Calculate the centroid and rotation differences between two contours.

       Args:
           workpieceContour (Contour): Contour object representing the workpieces contour.
           contour (Contour): Contour object representing the new contour.

       Returns:
           tuple: Centroid difference (numpy array) and rotation difference (float).
       """
    print(f"    Calculating differences")
    workpieceCentroid = workpieceContour.getCentroid()
    contourCentroid = contour.getCentroid()
    centroidDiff = np.array(contourCentroid) - np.array(workpieceCentroid)

    wpAngle = workpieceContour.getOrientation()
    contourAngle = contour.getOrientation()

    rotationDiff = contourAngle - wpAngle
    # if rotationDiff > 90:
    #     rotationDiff -= 180
    # elif rotationDiff < -90:
    #     rotationDiff += 180

    rotationDiff = (rotationDiff + 180) % 360 - 180  # Normalize to [-180, 180]

    from pathlib import Path

    # ... after computing wpAngle, contourAngle, rotationDiff ...
    debug_dir = Path(__file__).resolve().parent / "debug"
    debug_dir.mkdir(parents=True, exist_ok=True)
    file_path = debug_dir / "contour_debug.txt"

    with file_path.open("w", encoding="utf-8") as f:
        f.write(f"Workpiece orientation: {wpAngle}\n")
        f.write(f"Workpiece points: {workpieceContour.get_contour_points()}\n")
        f.write(f"Contour orientation: {contourAngle}\n")
        f.write(f"Contour points: {contour.get_contour_points()}\n")
        f.write(f"Calculated rotation difference: {rotationDiff}\n")

    print(f"Contour debug written to: {file_path}")
    return centroidDiff, rotationDiff, contourAngle


def _getSimilarity(contour1, contour2):
    """
     Calculate the similarity between two contours using shape matching.

     Args:
         contour1 (list): The first contour to compare.
         contour2 (list): The second contour to compare.

     Returns:
         float: The similarity score, as a percentage.
     """
    # Ensure contours are valid NumPy arrays with the correct shape

    contour1 = np.array(contour1, dtype=np.float32)
    contour2 = np.array(contour2, dtype=np.float32)

    # print("Contour1: ", contour1)
    # print("Contour2: ", contour2)

    similarity = cv2.matchShapes(contour1, contour2, cv2.CONTOURS_MATCH_I1, 0.0)
    similarityPercent = (1 - similarity) * 100
    return similarityPercent
