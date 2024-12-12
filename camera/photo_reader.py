import cv2
from pyzbar.pyzbar import decode

def read_qr_code(image_path):
    # Load the image from file
    frame = cv2.imread(image_path)
    
    # Decode QR codes from the image
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
    
    # Show the image with detected QR codes
    cv2.imshow("QR Code Scanner", frame)
    
    # Wait for key press to close the image window
    cv2.waitKey(0)
    cv2.destroyAllWindows()

# Example usage with an image file path
# image_path = "./qr_country_destination.png"
# image_path = "./qr_postal_code.png"
# image_path = "./qr_shipment.png"
image_path = "./qr_door.png"
read_qr_code(image_path)