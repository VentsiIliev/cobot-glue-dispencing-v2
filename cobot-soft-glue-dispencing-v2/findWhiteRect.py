import cv2
import numpy as np

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Convert to HSV (better for color detection)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Define white color range
    lower_white = np.array([0, 0, 160])
    upper_white = np.array([220, 50, 255])
    mask = cv2.inRange(hsv, lower_white, upper_white)

    # Optional: remove noise
    mask = cv2.medianBlur(mask, 5)

    # Find contours
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    largest_area = 0
    largest_rect = None

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        area = w * h
        if area > largest_area:
            largest_area = area
            largest_rect = (x, y, w, h)

    # Draw the largest rectangle
    if largest_rect is not None:
        x, y, w, h = largest_rect
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

    cv2.imshow("Largest White Rectangle", frame)
    cv2.imshow("Mask", mask)  # Useful for debugging

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
