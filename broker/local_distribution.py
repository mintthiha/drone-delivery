from datetime import datetime
from pathlib import Path
import paho.mqtt.client as mqtt
import json
import time
import requests
import threading

from jwt_module import generate_jwt

#Cryptography
import base64
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.serialization import load_pem_public_key, load_pem_private_key

broker_address = "localhost"
port = 1883 
# This makes sure if this client's public key is sent
isKeySent = False
# Flask API URL for posting messages
FLASK_API_URL = "http://localhost:5000/api"

UPC_IDS = ["UPC_1", "UPC_2", "UPC_3"]

#JWT Tokens for Distribution_carrier and here
distri_tokens = {
    "UPC_1": "N/A",
    "UPC_2": "N/A",
    "UPC_3": "N/A"
}

#JWT Tokens for SellerAPI and here
api_tokens = {
    "UPC_1": "N/A",
    "UPC_2": "N/A",
    "UPC_3": "N/A"
}

# Topics
send_topic = "test/topic1"
dashboard_topic = "dashboard/topic"
receive_topic = "test/topic2"

###### GENERATE KEY PAIR
def generate_key_pair():
    key_size = 2048  # Should be at least 2048

    private_key = rsa.generate_private_key(
        public_exponent=65537,  # Do not change
        key_size=key_size,
    )

    public_key = private_key.public_key()
    return private_key, public_key

# A - Generate for each node a key pair
private_key, public_key = generate_key_pair()

# B - Store public & private key as a file (.pem) -> other client will ONLY extract public key.
###### STORE PUBLIC AND PRIVATE KEY
password = b"local_distribution"
# private
key_pem_bytes = private_key.private_bytes(
   encoding=serialization.Encoding.PEM,  # PEM Format is specified
   format=serialization.PrivateFormat.PKCS8,
   encryption_algorithm=serialization.BestAvailableEncryption(password),
)
key_pem_path = Path("./local_keys/local_private_key.pem")
key_pem_path.write_bytes(key_pem_bytes)
# public
public_key = private_key.public_key()
public_pem_bytes = public_key.public_bytes(
   encoding=serialization.Encoding.PEM,
   format=serialization.PublicFormat.SubjectPublicKeyInfo,
)
public_pem_path = Path("./local_keys/local_public_key.pem")
public_pem_path.write_bytes(public_pem_bytes)

# X - Generate a public key (.pem) from other client when it is publishing
# We need the public key of the other Client to verify signature
def generateForeignPrimaryKey(nodename, publickey):
    public_pem_bytes = publickey.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    public_pem_path = Path(f"./local_keys/{nodename}_public_key.pem")
    public_pem_path.write_bytes(public_pem_bytes)

# D - Used in publish to encrypt the public key and encrypt payload messages
def encrypt(message, public_key):
    return public_key.encrypt(
        message,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

def verify(signature, message, public_key):
    try:
        public_key.verify(
            signature,
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except InvalidSignature:
        return False
    # "The signature, the message or the Public Key is invalid"

def decrypt(message_encrypted, private_key):
    try:
        message_decrypted = private_key.decrypt(
            message_encrypted,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return message_decrypted
    except ValueError:
        return "nothing"

# Helper function to publish a message
def publish_message(message,UPC_ID):
    global isKeySent, tokens
    if isKeySent == False: # Makes sure that destination client stores the pubkey
        print("Delivering key")
        #find carrier pub key
        public_pem_bytes = Path("./carrier_keys/carrier_public_key.pem").read_bytes()
        #find local_destination pubkey to send 
        public_pem_bytes_local = Path("./local_keys/local_public_key.pem").read_bytes()
        # Deserialize the PEM bytes into a public key object
        carrier_public_key = load_pem_public_key(public_pem_bytes)
        encrypted_fingerprint = encrypt(b"hello carrier", carrier_public_key)
        
        # Convert the encrypted fingerprint and public key to Base64 for JSON compatibility
        encrypted_fingerprint_b64 = base64.b64encode(encrypted_fingerprint).decode('utf-8')
        local_public_key_b64 = base64.b64encode(public_pem_bytes_local).decode('utf-8')

        client.publish(send_topic, json.dumps({"message": encrypted_fingerprint_b64, "public_key":local_public_key_b64, "node_name":"local"}))
        # client.publish(dashboard_topic, json.dumps({"UPC_ID": UPC_ID, "data": message}))
        print("Key is created inside the client destination")
        isKeySent = True
    else: # Every published message comes with a signature
        if message is not None:
            if distri_tokens[UPC_ID] == 'N/A':
              distri_tokens[UPC_ID] = generate_jwt(UPC_ID)

            # Read the local private key for signing
            private_key_pem = Path("./local_keys/local_private_key.pem").read_bytes()
            private_key = load_pem_private_key(private_key_pem, password=b"local_distribution")
            public_pem_bytes = Path("./carrier_keys/carrier_public_key.pem").read_bytes()
            carrier_public_key = load_pem_public_key(public_pem_bytes)
            dashboard_message = message
            
            # Serialize the message (if it's a dict)
            if isinstance(message, dict):
                message = json.dumps(message)  # Convert dictionary to a JSON string

            # Encrypt the message
            encrypted_message = encrypt(message.encode('utf-8'), carrier_public_key)
            
            # Sign the encrypted message
            signature = private_key.sign(
                encrypted_message,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            
            # Base64 encode the signature and message
            signature_b64 = base64.b64encode(signature).decode('utf-8')
            message_b64 = base64.b64encode(encrypted_message).decode('utf-8')
            
            time.sleep(2)
            # Publish the signed message
            client.publish(send_topic, json.dumps({
                "UPC_ID": UPC_ID,
                "data": message_b64,
                "signature": signature_b64,
                "node_name": "local",
                "token": distri_tokens[UPC_ID]
            }))
            client.publish(dashboard_topic, json.dumps({
                "UPC_ID": UPC_ID,
                "data": dashboard_message,
                "token": distri_tokens[UPC_ID]
            }))

# Callback function for when a message is received
# Updated callback function for when a message is received
def on_message(client, userdata, message):
    try:
        # Decode the payload and load it as JSON
        data = json.loads(message.payload.decode("utf-8"))
        
        # Verify signature
        public_pem_bytes = Path("./carrier_keys/carrier_public_key.pem").read_bytes()
        carrier_public_key = load_pem_public_key(public_pem_bytes)
        signature = base64.b64decode(data.get("signature"))
        message_data = base64.b64decode(data.get("data"))
        
        if verify(signature,message_data,carrier_public_key):
            print("Signature is Valid")
            
            private_pem_bytes = Path("./local_keys/local_private_key.pem").read_bytes()
            # Convert bytes to private key
            local_private_key = load_pem_private_key(private_pem_bytes, password=b"local_distribution")
            # decrypts data
            decrypt_data = decrypt(message_data,local_private_key)
            
            UPC_ID = data.get("UPC_ID")
            step = decrypt_data
            
            if step == b'Step3':
                # Step 5
                headers = {"Authorization": distri_tokens[UPC_ID]}
                response = requests.get(f"{FLASK_API_URL}/order/{UPC_ID}/door_destination", headers = headers)
                response_data = response.json() if response.status_code == 200 else None
                # Step 6
                publish_message(response_data, UPC_ID)
                
            elif step == b'Step8':
                # Step 9
                headers = {"Authorization": distri_tokens[UPC_ID]}
                response = requests.get(f"{FLASK_API_URL}/order/{UPC_ID}/postalcode_destination", headers = headers)
                response_data = response.json() if response.status_code == 200 else None
                # Step 10
                publish_message(response_data, UPC_ID)
            
    except json.JSONDecodeError:
        print("Failed to decode JSON data.")


client = mqtt.Client(client_id="Client1")
client.username_pw_set(username="testuser", password="pass1")
client.on_message = on_message

client.connect(broker_address, port)
client.subscribe(receive_topic)
client.loop_start()
# Function to fetch data for a specific UPC
def fetch_data_for_upc(UPC_ID):
    if api_tokens[UPC_ID] == 'N/A':
      api_tokens[UPC_ID] = generate_jwt(UPC_ID)
    
    headers = {"Authorization": api_tokens[UPC_ID]}
    response = requests.get(f"{FLASK_API_URL}/order/{UPC_ID}/country_destination", headers=headers)
    responseForPostalCode = requests.get(f"{FLASK_API_URL}/order/{UPC_ID}/postalcode_destination", headers = headers)

    if response.status_code == 200 and responseForPostalCode.status_code == 200:
        response_data = response.json()
        postalcode_data = responseForPostalCode.json()
        response_data['postalcode'] = postalcode_data.get('postal_code') 
     
        # Publish the message for this UPC
        publish_message(response_data,UPC_ID)
    else:
        print(f"Error fetching data for {UPC_ID} from the API.")

# Threading function to run fetch operations concurrently
def fetch_data_concurrently():
    threads = []
    for UPC_ID in UPC_IDS:
        thread = threading.Thread(target=fetch_data_for_upc, args=(UPC_ID,))
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

# Call the function to fetch data concurrently
publish_message(None,'publish_public_key')
fetch_data_concurrently()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    client.loop_stop()
    client.disconnect()
