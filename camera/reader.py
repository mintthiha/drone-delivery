import cv2
from picamera2 import Picamera2
from pyzbar.pyzbar import decode
import time

# Initialize Picamera2
picam2 = Picamera2()
config = picam2.create_preview_configuration(main={"size": (640, 480)})
picam2.configure(config)
picam2.start()

time.sleep(2)  # Allow time for the camera to warm up

def read_qr_code(frame):
    qr_codes = decode(frame)
    for qr_code in qr_codes:
        (x, y, w, h) = qr_code.rect
        # Draw a rectangle around the QR code
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        qr_data = qr_code.data.decode("utf-8")
        qr_type = qr_code.type
        # Display the QR code data and type
        text = f"Data: {qr_data} ({qr_type})"
        cv2.putText(frame, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        print(f"Found QR code: {qr_data} of type: {qr_type}")

while True:
    frame = picam2.capture_array()  # Capture the image
    read_qr_code(frame)             # Read and decode QR codes
    cv2.imshow("QR Code Scanner", frame)
    
    # Exit if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Cleanup
cv2.destroyAllWindows()
picam2.stop()
