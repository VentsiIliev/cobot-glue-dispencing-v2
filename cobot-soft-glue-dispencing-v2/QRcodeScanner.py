import cv2
from pyzbar.pyzbar import decode
from VisionSystem.VisionSystem import VisionSystem  # Unused in this example but left in for context

import re

def parse_data(data_str):
    pattern = r"id\s*=\s*(\S+)\s+password\s*=\s*(\S+)"
    match = re.search(pattern, data_str)
    if match:
        return {
            "id": match.group(1),
            "password": match.group(2)
        }
    return None

def detect_and_decode_qrcode(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    qrcodes = decode(gray)
    print("QR Codes Found:", len(qrcodes))

    for code in qrcodes:
        if code.type != "QRCODE":
            continue  # Skip non-QR codes

        data = code.data.decode("utf-8")
        (x, y, w, h) = code.rect

        # Draw bounding box and label
        cv2.rectangle(image, (x, y), (x + w, y + h), (255, 0, 0), 2)
        cv2.putText(image, f"{data} (QR)", (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        return data  # Return the first detected QR code
    return None

def main():
    cap = cv2.VideoCapture(2)  # Use your actual camera index

    if not cap.isOpened():
        print("Error: Could not open camera.")
        return

    print("Press 'q' to quit.")
    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        decoded = detect_and_decode_qrcode(frame)
        if decoded:
            # print("Decoded QR Code:", decoded)
            parsed = parse_data(decoded)
            if parsed:
                print(f"Parsed ID: {parsed['id']}, Password: {parsed['password']}")
            else:
                print("Failed to parse QR code data")

        cv2.imshow("QR Code Scanner", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
