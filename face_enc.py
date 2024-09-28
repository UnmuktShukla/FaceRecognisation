import cv2
import os
import face_recognition
from eth_account import Account
from web3 import Web3

# Connect to Ethereum Sepolia Testnet using Infura
w3 = Web3(Web3.HTTPProvider('https://sepolia.infura.io/v3/dec921727a714309879607891a0f03e0'))

# Load Ethereum account from private key
private_key = '0x'+'d5d060305f6895a15a48efcfbd5b41eeed1f2a10a8a3ce424e54c812d07fbb88'
account = Account.from_key(private_key)

# Address of your deployed smart contract
contract_address = '0x1bDF9d23879c0be50bB047c5a4fAEC5FD7125091'

# Load the contract ABI (Application Binary Interface)
with open('path_to_contract_abi.json') as f:
    contract_abi = f.read()

# Instantiate the contract
contract = w3.eth.contract(address=contract_address, abi=contract_abi)

# Load known face images and encode them
known_face_encodings = []
known_face_names = []

# Directory where your known images are stored
known_faces_dir = "known_faces"

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

# Function to sign the user's identity using Ethereum's account
def sign_identity(identity_data):
    # Create a keccak256 hash of the identity data
    identity_hash = Web3.keccak(text=identity_data)
    # Sign the identity hash using the private key
    signed_message = account.sign_message(identity_hash)
    return signed_message

# Function to send a transaction to the blockchain
def send_transaction(function, *args):
    # Prepare the transaction
    transaction = function(*args).buildTransaction({
        'from': account.address,
        'nonce': w3.eth.getTransactionCount(account.address),
        'gas': 2000000,
        'gasPrice': w3.toWei('20', 'gwei')
    })

    # Sign the transaction
    signed_txn = account.sign_transaction(transaction)

    # Send the signed transaction
    txn_hash = w3.eth.sendRawTransaction(signed_txn.rawTransaction)

    # Wait for the transaction to be mined
    txn_receipt = w3.eth.waitForTransactionReceipt(txn_hash)

    return txn_receipt

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

            # Sign the identity and send it to the blockchain
            signed_identity = sign_identity(name)
            txn_receipt = send_transaction(contract.functions.registerIdentity, signed_identity.messageHash)
            print(f"Identity for {name} registered with transaction hash: {txn_receipt.transactionHash.hex()}")

        # Draw a rectangle around the face
        cv2.rectangle(frame, (left, top), (right, bottom), box_color, 2)

        # Draw a label with the name below the face
        cv2.rectangle(frame, (left, bottom - 35), (right, bottom), box_color, cv2.FILLED)
        cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 1.0, (255, 255, 255), 1)

    # Display the resulting frame
    cv2.imshow('Face Recognition and Identity Verification', frame)

    # Break the loop on 'q' key press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the camera and close windows
cap.release()
cv2.destroyAllWindows()
