from __future__ import annotations

import numpy as np
from PyQt6.QtCore import QPointF
import copy
from pl_gui.contour_editor.SegmentSettingsWidget import default_settings


class Segment:
    def __init__(self, layer=None):
        self.points: list[QPointF] = []
        self.controls: list[QPointF | None] = []
        self.visible = True
        self.layer = layer
        self.settings = default_settings
        print("Setting default settings:", self.settings)

    def set_settings(self, settings: dict):
        """Set the settings for the segment."""
        self.settings = settings
        print("Segment settings updated:", self.settings)

    def add_point(self, point: QPointF):
        self.points.append(point)
        if len(self.points) > 1:
            self.controls.append(None)

    def remove_point(self, index: int):
        if 0 <= index < len(self.points):
            del self.points[index]
            if index < len(self.controls):
                del self.controls[index]

    def add_control_point(self, index: int, point: QPointF):
        if 0 <= index < len(self.controls):
            self.controls[index] = point
        else:
            self.controls.append(point)

    def set_layer(self, layer):
        self.layer = layer

    def get_external_layer(self):
        return self.layer if self.layer else None

    def get_contour_layer(self):
        return self.layer if self.layer else None

    def get_fill_layer(self):
        return self.layer if self.layer else None

    def __str__(self):
        return f"Segment(points={self.points}, controls={self.controls}, visible={self.visible}, layer={self.layer})"


class Layer:
    def __init__(self, name, locked=False, visible=True):
        self.name = name
        self.locked = locked
        self.visible = visible
        self.segments: list[Segment] = []

    def add_segment(self, segment: Segment):
        self.segments.append(segment)

    def remove_segment(self, index: int):
        if 0 <= index < len(self.segments):
            del self.segments[index]

    def __str__(self):
        return f"Layer(name={self.name}, locked={self.locked}, visible={self.visible}, segments={self.segments})"


class BezierSegmentManager:
    def __init__(self):
        self.active_segment_index = 0
        self.undo_stack = []
        self.redo_stack = []
        self.external_layer = Layer("External", True, True)
        self.contour_layer = Layer("Contour", False, True)
        self.fill_layer = Layer("Fill", False, True)
        self.segments: list[Segment] = [Segment(layer=self.contour_layer)]

    def undo(self):
        if not self.undo_stack:
            raise Exception("Nothing to undo.")
        self.redo_stack.append(copy.deepcopy(self.segments))
        self.segments = self.undo_stack.pop()

    def redo(self):
        if not self.redo_stack:
            raise Exception("Nothing to redo.")
        self.undo_stack.append(copy.deepcopy(self.segments))
        self.segments = self.redo_stack.pop()

    def save_state(self, max_stack_size=100):
        print("Saving state...")
        self.undo_stack.append(copy.deepcopy(self.segments))
        if len(self.undo_stack) > max_stack_size:
            self.undo_stack.pop(0)
        self.redo_stack.clear()

    def set_active_segment(self, seg_index):
        if 0 <= seg_index < len(self.segments):
            segment = self.segments[seg_index]
            layer_name = getattr(segment, 'layer', None)

            # Check if the segment has a layer and if it's locked
            if layer_name:
                if ((layer_name == "External" and self.external_layer.locked) or
                        (layer_name == "Contour" and self.contour_layer.locked) or
                        (layer_name == "Fill" and self.fill_layer.locked)):
                    print(f"Cannot activate segment {seg_index}: Layer '{layer_name}' is locked.")
                    return

            print(f"Updating segment: {seg_index}")
            self.active_segment_index = seg_index



    def create_segment(self, points, layer_name="Contour"):
        # Select the correct layer object
        if layer_name == "External":
            layer = self.external_layer
        elif layer_name == "Contour":
            layer = self.contour_layer
        elif layer_name == "Fill":
            layer = self.fill_layer
        else:
            raise ValueError(f"Invalid layer name: {layer_name}")

        # Create the segment and add points
        segment = Segment(layer=layer)
        for pt in points:
            segment.add_point(pt)
        return segment

    def start_new_segment(self, layer=None):
        print("Existing segments before creation:", len(self.segments))
        print("Starting new segment...")

        # Existing segment checking
        if len(self.segments) > 0:
            print("Existing segment:", self.segments[0])

        # Lock check logic and segment creation
        if layer:
            print(f"Layer {layer} check...")
            if layer == "External" and self.external_layer.locked:
                print(f"Cannot start new segment: Layer '{layer}' is locked.")
                return
            elif layer == "Contour" and self.contour_layer.locked:
                print(f"Cannot start new segment: Layer '{layer}' is locked.")
                return
            elif layer == "Fill" and self.fill_layer.locked:
                print(f"Cannot start new segment: Layer '{layer}' is locked.")
                return

        if layer == "External":
            layer = self.external_layer
        elif layer == "Contour":
            layer = self.contour_layer
        elif layer == "Fill":
            layer = self.fill_layer
        else:
            print(f"Invalid layer name: {layer}")
            return



        # Create the segment
        new_segment = Segment(layer=layer)
        print(f"Created new segment: {new_segment}")
        self.segments.append(new_segment)
        self.active_segment_index = len(self.segments) - 1
        return new_segment

    def assign_segment_layer(self, seg_index, layer_name):

        segment = self.segments[seg_index]
        if segment.layer.locked:
            print(f"Cannot assign layer: Layer '{segment.layer.name}' is locked.")
            return

        if 0 <= seg_index < len(self.segments):
            if layer_name == "External":
                segment.layer = self.external_layer
            elif layer_name == "Contour":
                segment.layer = self.contour_layer
            elif layer_name == "Fill":
                segment.layer = self.fill_layer
            else:
                print(f"Invalid layer name: {layer_name}")
                return

    def add_point(self, pos: QPointF):
        if 0 <= self.active_segment_index < len(self.segments):
            self.save_state()
            active_segment = self.segments[self.active_segment_index]

            if active_segment.layer is None:
                print("Cannot add point: Segment layer is not set.")
                return

            # Check if the layer is locked
            if active_segment.layer.locked:
                print(f"Cannot add point: Layer '{active_segment.layer.name}' is locked.")
                return  # Exit the function if the layer is locked

            active_segment.add_point(pos)  # Corrected the syntax here
            print(f"Added point {pos} to segment {self.active_segment_index}")

    def get_segments(self):
        return self.segments

    def to_wp_data(self, samples_per_segment=5):
        path_points = {
            "External": [],
            "Contour": [],
            "Fill": []
        }

        def is_cp_effective(p0, cp, p1, threshold=1.0):
            dx, dy = p1.x() - p0.x(), p1.y() - p0.y()
            if dx == dy == 0:
                return False
            distance = abs(dy * cp.x() - dx * cp.y() + p1.x() * p0.y() - p1.y() * p0.x()) / ((dx ** 2 + dy ** 2) ** 0.5)
            return distance > threshold

        def to_opencv_contour(path):
            """Convert list of [x, y] points to OpenCV-style contour array"""
            if not path or not all(isinstance(pt, (list, tuple)) and len(pt) == 2 for pt in path):
                print("⚠️ Skipping invalid path:", path)
                return None
            return np.array(path, dtype=np.float32).reshape(-1, 1, 2)

        # Process each segment individually
        for segment in self.segments:
            raw_path = []
            points = segment.points
            controls = segment.controls

            # Add the first point
            if points:
                raw_path.append([points[0].x(), points[0].y()])

            # Build the path for this segment
            for i in range(1, len(points)):
                p0, p1 = points[i - 1], points[i]
                if i - 1 < len(controls) and controls[i - 1] is not None and is_cp_effective(p0, controls[i - 1], p1):
                    # For Bezier curves, skip t=0 (which is p0, already added) and include t=1 (which is p1)
                    for t in [j / samples_per_segment for j in range(1, samples_per_segment + 1)]:
                        x = (1 - t) ** 2 * p0.x() + 2 * (1 - t) * t * controls[i - 1].x() + t ** 2 * p1.x()
                        y = (1 - t) ** 2 * p0.y() + 2 * (1 - t) * t * controls[i - 1].y() + t ** 2 * p1.y()
                        raw_path.append([x, y])
                else:
                    # For straight lines, only add p1 (p0 is already in the path)
                    raw_path.append([p1.x(), p1.y()])

            # Convert to OpenCV contour format
            contour = to_opencv_contour(raw_path)
            if contour is not None:
                # Append a new contour-settings pair for this segment
                path_points[segment.layer.name].append({
                    "contour": contour,
                    "settings": dict(segment.settings)
                })

        # Add placeholders for layers that have no segments
        for layer_name in ["External", "Contour", "Fill"]:
            if not path_points[layer_name]:
                path_points[layer_name].append({
                    "contour": np.empty((0, 1, 2), dtype=np.float32),
                    "settings": {}
                })

        print("path_points in to_wp_data:", path_points)
        return path_points
    # Example implementation for BezierSegmentManager
    def get_active_segment(self):
        if self.active_segment_index is not None and 0 <= self.active_segment_index < len(self.segments):
            return self.segments[self.active_segment_index]
        return None
    # def to_wp_data(self, samples_per_segment=5):
    #     path_points = {"External": [],
    #                    "Contour": [],
    #                    "Fill": []}
    #
    #     def is_cp_effective(p0, cp, p1, threshold=1.0):
    #         dx, dy = p1.x() - p0.x(), p1.y() - p0.y()
    #         if dx == dy == 0:
    #             return False
    #         distance = abs(dy * cp.x() - dx * cp.y() + p1.x() * p0.y() - p1.y() * p0.x()) / ((dx ** 2 + dy ** 2) ** 0.5)
    #         return distance > threshold
    #
    #     for segment in self.segments:
    #         path = []
    #         points = segment.points
    #         controls = segment.controls
    #         for i in range(1, len(points)):
    #             p0, p1 = points[i - 1], points[i]
    #             if i - 1 < len(controls) and controls[i - 1] is not None and is_cp_effective(p0, controls[i - 1], p1):
    #                 for t in [j / samples_per_segment for j in range(samples_per_segment + 1)]:
    #                     x = (1 - t) ** 2 * p0.x() + 2 * (1 - t) * t * controls[i - 1].x() + t ** 2 * p1.x()
    #                     y = (1 - t) ** 2 * p0.y() + 2 * (1 - t) * t * controls[i - 1].y() + t ** 2 * p1.y()
    #                     # path.append(QPointF(x, y))
    #                     path.append([x, y])  # <- change here
    #             else:
    #                 # path.extend([p0, p1])
    #                 path.extend([[p.x(), p.y()] for p in [p0, p1]])  # <- and here
    #
    #         path_points[segment.layer.name] = path
    #
    #     return path_points



    def get_robot_path(self, samples_per_segment=5):
        path_points = []

        def is_cp_effective(p0, cp, p1, threshold=1.0):
            dx, dy = p1.x() - p0.x(), p1.y() - p0.y()
            if dx == dy == 0:
                return False
            distance = abs(dy * cp.x() - dx * cp.y() + p1.x() * p0.y() - p1.y() * p0.x()) / ((dx ** 2 + dy ** 2) ** 0.5)
            return distance > threshold

        for segment in self.segments:
            points = segment.points
            controls = segment.controls
            for i in range(1, len(points)):
                p0, p1 = points[i - 1], points[i]
                if i - 1 < len(controls) and controls[i - 1] is not None and is_cp_effective(p0, controls[i - 1], p1):
                    for t in [j / samples_per_segment for j in range(samples_per_segment + 1)]:
                        x = (1 - t) ** 2 * p0.x() + 2 * (1 - t) * t * controls[i - 1].x() + t ** 2 * p1.x()
                        y = (1 - t) ** 2 * p0.y() + 2 * (1 - t) * t * controls[i - 1].y() + t ** 2 * p1.y()
                        path_points.append(QPointF(x, y))
                else:
                    path_points.extend([p0, p1])

        return path_points

    def delete_segment(self, seg_index):
        if 0 <= seg_index < len(self.segments):

            segment = self.segments[seg_index]

            if segment.layer.locked:
                print(f"Cannot delete segment {seg_index}: Layer '{segment.layer.name}' is locked.")
                return
            # # Check if the segment has a layer and if it's locked
            # layer_name = getattr(segment, 'layer', None)
            # if layer_name:
            #     if ((layer_name == "External" and self.external_layer.locked) or
            #             (layer_name == "Contour" and self.contour_layer.locked) or
            #             (layer_name == "Fill" and self.fill_layer.locked)):
            #         print(f"Cannot delete segment {seg_index}: Layer '{layer_name}' is locked.")
            #         return

            del self.segments[seg_index]
            if not self.segments:
                self.active_segment_index = -1
            elif self.active_segment_index == seg_index:
                self.active_segment_index = len(self.segments) - 1
            elif self.active_segment_index > seg_index:
                self.active_segment_index -= 1

    def set_segment_visibility(self, seg_index, visible):
        if 0 <= seg_index < len(self.segments):
            self.segments[seg_index].visible = visible

    def is_segment_visible(self, seg_index):
        if 0 <= seg_index < len(self.segments):
            return self.segments[seg_index].visible
        return False

    def has_control_points(self, seg_index):
        if 0 <= seg_index < len(self.segments):
            return len(self.segments[seg_index].controls) > 0
        return False

    def find_drag_target(self, pos, threshold=10):
        for seg_index, seg in enumerate(self.segments):
            # Check control points
            for i, pt in enumerate(seg.controls):
                if pt is None:
                    continue  # Skip placeholder controls
                if (pt - pos).manhattanLength() < threshold:
                    return 'control', seg_index, i

            # Check anchor points
            for i, pt in enumerate(seg.points):
                if (pt - pos).manhattanLength() < threshold:
                    return 'anchor', seg_index, i

        return None

    def reset_control_point(self, seg_index, ctrl_idx):
        self.save_state()
        segment = self.segments[seg_index]

        # Sanity check
        if 0 <= ctrl_idx < len(segment.controls) and ctrl_idx < len(segment.points):
            segment.controls[ctrl_idx] = QPointF(segment.points[ctrl_idx])

    def move_point(self, role, seg_index, idx, new_pos, suppress_save=False):
        if not suppress_save:
            self.save_state()

        segment = self.segments[seg_index]

        if segment.layer.locked:
            print(f"Cannot move point: Layer '{segment.layer.name}' is locked.")
            return

        points = segment.points  # Access the 'points' attribute
        controls = segment.controls  # Access the 'controls' attribute

        if role == 'anchor':
            old_pos = points[idx]
            delta = new_pos - old_pos
            points[idx] = new_pos

            if idx > 0 and idx - 1 < len(controls):
                p0, ctrl = points[idx - 1], controls[idx - 1]
                if self.is_on_line(p0, ctrl, old_pos):
                    controls[idx - 1] = (p0 + new_pos) / 2

            if idx < len(points) - 1 and idx < len(controls):
                p1, ctrl = points[idx + 1], controls[idx]
                if self.is_on_line(old_pos, ctrl, p1):
                    controls[idx] = (new_pos + p1) / 2

        elif role == 'control':
            controls[idx] = new_pos

    def remove_control_point_at(self, pos, threshold=10):
        self.save_state()
        for seg in self.segments:

            if seg.layer is None:
                print("Cannot remove control point: Segment layer is not set.")
                return False

            if seg.layer.locked:
                print(f"Cannot remove control point: Layer '{seg.layer.name}' is locked.")
                return False

            for i, pt in enumerate(seg.controls):  # Access the 'controls' attribute
                if pt is None:  # Skip placeholder controls
                    continue
                if (pt - pos).manhattanLength() < threshold:
                    seg.remove_point(i)  # Access 'remove_point' method
                    # del seg.controls[i]  # Access 'controls' and delete the control point
                    if i + 1 < len(seg.points):  # Access 'points' and delete the corresponding point
                        del seg.points[i + 1]
                    return True
        return False

    def remove_point(self, role, seg_index, idx):
        self.save_state()
        segment = self.segments[seg_index]

        # Check if the segment has a layer and if it's locked
        layer_name = getattr(segment, 'layer', None)
        if layer_name:
            if ((layer_name == "External" and self.external_layer.locked) or
                    (layer_name == "Contour" and self.contour_layer.locked) or
                    (layer_name == "Fill" and self.fill_layer.locked)):
                print(f"Cannot remove point: Layer '{layer_name}' is locked.")
                return

        if role == 'anchor':
            del segment.points[idx]  # Access the 'points' attribute
        elif role == 'control':
            del segment.controls[idx]  # Access the 'controls' attribute
        else:
            raise ValueError("Role must be 'anchor' or 'control'")

    @staticmethod
    def is_on_line(p0, cp, p1, threshold=1.0):
        if cp is None:
            return False

        dx = p1.x() - p0.x()
        dy = p1.y() - p0.y()

        if dx == 0 and dy == 0:
            return False

        # Vector from p0 to cp
        v1x = cp.x() - p0.x()
        v1y = cp.y() - p0.y()

        # Vector from p0 to p1
        v2x = dx
        v2y = dy

        # Dot product to check if cp is within the segment projection
        dot = v1x * v2x + v1y * v2y
        len_sq = v2x * v2x + v2y * v2y

        if dot < 0 or dot > len_sq:
            return False  # cp lies outside the segment

        # Perpendicular distance from cp to line p0-p1
        distance = abs(dy * cp.x() - dx * cp.y() + p1.x() * p0.y() - p1.y() * p0.x()) / ((dx ** 2 + dy ** 2) ** 0.5)

        return distance < threshold

    def add_control_point(self, segment_index, pos):
        self.save_state()  # Save the state before any changes

        # Retrieve the segment and check if it has a layer
        segment = self.segments[segment_index]

        if segment.layer.locked:
            print(f"Cannot add control point: Layer '{segment.layer.name}' is locked.")
            return False  # Return early if layer is locked

        # Proceed with finding the segment at the position and adding control point
        segment_info = self.find_segment_at(pos)
        if not segment_info:
            print("No segment line clicked.")
            return False

        seg_index, line_index = segment_info
        p0 = segment.points[line_index]
        p1 = segment.points[line_index + 1]

        midpoint = (p0 + p1) * 0.5
        print(f"Adding control point at midpoint {midpoint} between {p0} and {p1}")
        print(f"Segment layer locked: ",segment.layer.locked)
        if line_index < len(segment.controls):
            segment.controls[line_index] = midpoint
        else:
            # Ensure the controls list matches the number of line segments
            while len(segment.controls) < line_index:
                segment.controls.append(None)
            segment.controls.append(midpoint)

        return True

    def find_segment_at(self, pos, threshold=10):
        for seg_index, segment in enumerate(self.segments):
            points = segment.points
            for i in range(1, len(points)):
                p0 = points[i - 1]
                p1 = points[i]

                if self.is_on_segment(p0, pos, p1, threshold):
                    return seg_index, i - 1

        return None

    @staticmethod
    def is_on_segment(p0, test_pt, p1, threshold=5.0):
        if test_pt is None:
            return False

        dx = p1.x() - p0.x()
        dy = p1.y() - p0.y()
        segment_length_squared = dx * dx + dy * dy
        if segment_length_squared == 0:
            return False

        # Vector from p0 to test_pt
        px = test_pt.x() - p0.x()
        py = test_pt.y() - p0.y()

        # Projection scalar
        t = (px * dx + py * dy) / segment_length_squared

        if t < 0.0 or t > 1.0:
            return False

        # Projection point on the segment
        proj_x = p0.x() + t * dx
        proj_y = p0.y() + t * dy

        # Distance from test point to projection
        dist = ((test_pt.x() - proj_x) ** 2 + (test_pt.y() - proj_y) ** 2) ** 0.5

        return dist <= threshold

    def set_layer_locked(self, layer_name, locked):
        if layer_name == "External":
            self.external_layer.locked = locked
        elif layer_name == "Contour":
            self.contour_layer.locked = locked
        elif layer_name == "Fill":
            self.fill_layer.locked = locked
        print("Layer lock state updated:", layer_name, locked)

    def isLayerLocked(self, layer_name):
        if layer_name == "External":
            return self.external_layer.locked
        elif layer_name == "Contour":
            return self.contour_layer.locked
        elif layer_name == "Fill":
            return self.fill_layer.locked
        return

    def contour_to_bezier(self,contour, control_point_ratio=0.5, close_contour=True):
        """
        Converts a contour to a single Segment with Bezier control points.

        Args:
            contour (list or numpy array): OpenCV-style contour [[x, y]].
            control_point_ratio (float): Where to place the control point between two anchor points.
            close_contour (bool): Whether to close the contour if it's not already.

        Returns:
            List[Segment]: A single Segment object containing all anchor and control points.
        """
        if len(contour) < 2:
            return []

        # Check for closure if requested
        if close_contour:
            start_pt = contour[0][0]
            end_pt = contour[-1][0]
            if not np.allclose(start_pt, end_pt):  # Check if already closed
                contour = np.vstack([contour, [contour[0]]])  # Close it by adding first point to end

        self.external_layer.locked = False
        segment = Segment(self.external_layer)
        self.external_layer.locked = True
        # Add anchor points
        for pt in contour:
            point = QPointF(pt[0][0], pt[0][1])
            segment.add_point(point)

        # Add control points between each pair of consecutive anchor points
        for i in range(len(segment.points) - 1):
            p0 = segment.points[i]
            p1 = segment.points[i + 1]
            control_x = (1 - control_point_ratio) * p0.x() + control_point_ratio * p1.x()
            control_y = (1 - control_point_ratio) * p0.y() + control_point_ratio * p1.y()
            control_pt = QPointF(control_x, control_y)
            segment.add_control_point(i, control_pt)

        return [segment]
