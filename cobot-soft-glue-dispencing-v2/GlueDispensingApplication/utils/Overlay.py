import cv2
import numpy as np
from src.plvision.PLVision import Contouring


def drawWorkpieceId(frame, contour, id):
    overlay = frame.copy()
    alpha = 0.8  # Transparency factor
    # convert to numpy array
    contour = np.array(contour, dtype=np.int32).reshape(-1, 2)
    centroid = Contouring.calculateCentroid(contour)
    cv2.putText(overlay, f"ID: {id}", (int(centroid[0]), int(centroid[1])),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
    # Apply transparency (alpha blending)
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)


# def draw_overlay(frame, workpieces, contour):
#     drawWorkpieceId(frame, contour, workpieces.workpieceId)
#     overlay = frame.copy()
#     alpha = 0.8  # Transparency factor
#
#     # Define colors in BGR format
#     box_color = (179, 86, 0)  # Blue
#     text_color = (0, 0, 0)  # Black
#     background_color = (252, 209, 142)  # White
#     border_color = (218, 137, 114)  # Gray
#     shadow_color = (50, 50, 50)  # Dark Gray for shadow effect
#     gradient_start = (100, 100, 100)  # Darker gradient start (top)
#     gradient_end = (255, 255, 255)  # Lighter gradient end (bottom)
#
#     contour = np.array(contour, dtype=np.int32).reshape(-1, 2)  # Convert to int32 if not already
#
#     # Get bounding box of the contour
#     x, y, w, h = cv2.boundingRect(contour)
#
#     # Draw the object contour with a blue outline
#     # cv2.drawContours(frame, [contour], -1, box_color, 3)
#
#     # Prepare text details
#     font_scale = 0.6
#     font_thickness = 1
#     line_spacing = 25
#
#     details = [
#         f"ID: {workpieces.workpieceId} ",
#         f"Description: {workpieces.description}",
#         f"Program: {workpieces.program}",
#         f"Offset: {workpieces.offset}",
#         f"Height: {workpieces.height} mm",
#         f"Spray Type: {workpieces.sprayType}",
#         f"Glue Type: {workpieces.glueType}",
#         f"Material: {workpieces.material}",
#         f"Nozzles: {workpieces.nozzles}"
#     ]
#
#     # Determine the width of the longest line of text
#     text_widths = [cv2.getTextSize(line, cv2.FONT_HERSHEY_SIMPLEX, font_scale, font_thickness)[0][0] for line in
#                    details]
#     max_text_width = max(text_widths) + 20  # Add padding
#
#     # Set text box position next to the contour
#     text_background_x1 = x + w + 20
#     text_background_y1 = max(y, 10)
#     text_background_x2 = text_background_x1 + max_text_width
#     text_background_y2 = text_background_y1 + len(details) * line_spacing + 20
#
#     # Prevent text box from going off-screen (shift left if necessary)
#     frame_height, frame_width, _ = frame.shape
#     if text_background_x2 > frame_width - 10:
#         text_background_x1 = x - max_text_width - 20
#         text_background_x2 = text_background_x1 + max_text_width
#
#     if text_background_y2 > frame_height - 10:
#         text_background_y1 = frame_height - len(details) * line_spacing - 30
#         text_background_y2 = frame_height - 10
#
#     # Create a gradient effect for the background of the overlay
#     gradient = np.zeros((text_background_y2 - text_background_y1, text_background_x2 - text_background_x1, 3),
#                         dtype=np.uint8)
#     for i in range(gradient.shape[0]):
#         weight = i / gradient.shape[0]
#         gradient[i, :, :] = np.array([
#             (1 - weight) * gradient_start[0] + weight * gradient_end[0],
#             (1 - weight) * gradient_start[1] + weight * gradient_end[1],
#             (1 - weight) * gradient_start[2] + weight * gradient_end[2]
#         ], dtype=np.uint8)
#
#     # Place the gradient onto the overlay
#     overlay[text_background_y1:text_background_y2, text_background_x1:text_background_x2] = gradient
#
#     # Add shadow effect (darker rectangle behind the text box)
#     shadow_offset = 10  # Shadow offset
#     cv2.rectangle(overlay, (text_background_x1 + shadow_offset, text_background_y1 + shadow_offset),
#                   (text_background_x2 + shadow_offset, text_background_y2 + shadow_offset), shadow_color, -1,
#                   cv2.LINE_AA)
#
#     # Draw the main text box with the gradient background
#     cv2.rectangle(overlay, (text_background_x1, text_background_y1),
#                   (text_background_x2, text_background_y2), background_color, -1, cv2.LINE_AA)
#     cv2.rectangle(overlay, (text_background_x1, text_background_y1),
#                   (text_background_x2, text_background_y2), border_color, 2, cv2.LINE_AA)  # Gray border
#
#     # Apply transparency (alpha blending)
#     cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
#
#     # Put text on overlay
#     text_x = text_background_x1 + 10
#     text_y = text_background_y1 + 25
#     for line in details:
#         cv2.putText(frame, line, (text_x, text_y),
#                     cv2.FONT_HERSHEY_SIMPLEX, font_scale, text_color, font_thickness, cv2.LINE_AA)
#         text_y += line_spacing

def draw_overlay(frame, details, contour):
    drawWorkpieceId(frame, contour, details[0])
    overlay = frame.copy()
    alpha = 0.8  # Transparency factor

    # Define colors
    box_color = (179, 86, 0)  # Blue
    text_color = (0, 0, 0)  # Black
    background_color = (252, 209, 142)  # Light color
    border_color = (218, 137, 114)  # Gray border
    shadow_color = (50, 50, 50)  # Shadow effect
    x_button_color = (0, 0, 255)  # Red "X" button

    contour = np.array(contour, dtype=np.int32).reshape(-1, 2)

    # Get bounding box of the contour
    x, y, w, h = cv2.boundingRect(contour)

    # Prepare text details
    font_scale = 0.6
    font_thickness = 1
    line_spacing = 25



    # Determine text box size
    text_widths = [cv2.getTextSize(line, cv2.FONT_HERSHEY_SIMPLEX, font_scale, font_thickness)[0][0] for line in
                   details]
    max_text_width = max(text_widths) + 20

    # Set text box position
    text_background_x1 = x + w + 20
    text_background_y1 = max(y, 10)
    text_background_x2 = text_background_x1 + max_text_width
    text_background_y2 = text_background_y1 + len(details) * line_spacing + 40  # Extra space for "X" button

    # Ensure the box stays inside the frame
    frame_height, frame_width, _ = frame.shape
    if text_background_x2 > frame_width - 10:
        text_background_x1 = x - max_text_width - 20
        text_background_x2 = text_background_x1 + max_text_width

    if text_background_y2 > frame_height - 10:
        text_background_y1 = frame_height - len(details) * line_spacing - 50
        text_background_y2 = frame_height - 10

    # Draw shadow effect
    shadow_offset = 10
    cv2.rectangle(overlay, (text_background_x1 + shadow_offset, text_background_y1 + shadow_offset),
                  (text_background_x2 + shadow_offset, text_background_y2 + shadow_offset), shadow_color, -1,
                  cv2.LINE_AA)

    # Draw main overlay box
    cv2.rectangle(overlay, (text_background_x1, text_background_y1),
                  (text_background_x2, text_background_y2), background_color, -1, cv2.LINE_AA)
    cv2.rectangle(overlay, (text_background_x1, text_background_y1),
                  (text_background_x2, text_background_y2), border_color, 2, cv2.LINE_AA)

    # # Draw "X" button in the top-right corner of the box
    # x_button_size = 20
    # x_button_x1 = text_background_x2 - x_button_size - 5
    # x_button_y1 = text_background_y1 + 5
    # x_button_x2 = x_button_x1 + x_button_size
    # x_button_y2 = x_button_y1 + x_button_size

    # Draw "X" button background
    # cv2.rectangle(overlay, (x_button_x1, x_button_y1), (x_button_x2, x_button_y2), x_button_color, -1, cv2.LINE_AA)

    # Draw "X" symbol
    # cv2.line(overlay, (x_button_x1 + 4, x_button_y1 + 4), (x_button_x2 - 4, x_button_y2 - 4), (255, 255, 255), 2)
    # cv2.line(overlay, (x_button_x1 + 4, x_button_y2 - 4), (x_button_x2 - 4, x_button_y1 + 4), (255, 255, 255), 2)

    # Apply transparency
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

    # Put text on overlay
    text_x = text_background_x1 + 10
    text_y = text_background_y1 + 35  # Adjusted to avoid overlap with the "X" button
    for line in details:
        cv2.putText(frame, line, (text_x, text_y),
                    cv2.FONT_HERSHEY_SIMPLEX, font_scale, text_color, font_thickness, cv2.LINE_AA)
        text_y += line_spacing

