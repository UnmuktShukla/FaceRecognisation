import cv2
import os
import face_recognition
import hashlib
import os
from ecdsa import SigningKey, NIST384p

# Function to sign data using ECDSA
def sign_data(user_data, nonce):
    message = f"{user_data}:{nonce}".encode()
    sk = SigningKey.generate(curve=NIST384p)  # Generate a new signing key
    signature = sk.sign(message).hex()  # Create a signature
    return signature, sk

# Load known face images and encode them
known_face_encodings = []
known_face_names = []

# Directory where your known images are stored
known_faces_dir = "pushkar"

for file_name in os.listdir(known_faces_dir):
    if file_name.endswith(('.jpg', '.jpeg', '.png')):
        image_path = os.path.join(known_faces_dir, file_name)
        image = face_recognition.load_image_file(image_path)
        face_encoding = face_recognition.face_encodings(image)

        if face_encoding:  # Ensure at least one face encoding was found
            known_face_encodings.append(face_encoding[0])
            known_face_names.append(os.path.splitext(file_name)[0])  # Use file name as the person's name

# Initialize video capture
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open video.")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        print("Error: Failed to capture image.")
        break

    # Convert the frame from BGR to RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Find all faces and face encodings in the current frame
    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
        # Compare the detected face to known faces
        matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
        name = "Unknown"
        box_color = (0, 0, 255)  # Red for unknown faces

        # If a match is found, get the corresponding name
        if True in matches:
            first_match_index = matches.index(True)
            name = known_face_names[first_match_index]
            box_color = (0, 255, 0)  # Green for known faces

            # Generate a nonce
            nonce = os.urandom(16).hex()  # Random nonce for each recognition event
            # Sign the data
            signature, signing_key = sign_data(name, nonce)

            # Store the signature and nonce (you may want to store this on your blockchain)
            print(f"Signature for {name} with nonce {nonce}: {signature}")

        # Draw a rectangle around the face
        cv2.rectangle(frame, (left, top), (right, bottom), box_color, 2)

        # Draw a label with the name below the face
        cv2.rectangle(frame, (left, bottom - 35), (right, bottom), box_color, cv2.FILLED)
        cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 1.0, (255, 255, 255), 1)

    # Display the resulting frame
    cv2.imshow('Face Recognition', frame)

    # Break the loop on 'q' key press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the camera and close windows
cap.release()
cv2.destroyAllWindows()
