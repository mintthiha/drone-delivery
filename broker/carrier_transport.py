from pathlib import Path
import paho.mqtt.client as mqtt
import json
import requests
#Cryptography
import base64
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.serialization import load_pem_private_key, load_pem_public_key

from jwt_module import generate_jwt, validate_jwt

broker_address = "localhost"
port = 1883
send_topic = "test/topic2"
receive_topic = "test/topic1"

# Flask API URL for posting messages
FLASK_API_URL = "http://localhost:5001/api/shipment"

# States
current_state = {
    "UPC_1": {"status": "waiting"},
    "UPC_2": {"status": "waiting"},
    "UPC_3": {"status": "waiting"}
}

#Tokens between carrier and CarrierAPI
carrier_tokens = {
    "UPC_1": generate_jwt('UPC_1'),
    "UPC_2": generate_jwt('UPC_2'),
    "UPC_3": generate_jwt('UPC_3')
}

UPC_ID = 'UPC_1'

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

###### STORE PUBLIC AND PRIVATE KEY
password = b"carrier_transport"
# private
key_pem_bytes = private_key.private_bytes(
   encoding=serialization.Encoding.PEM,  # PEM Format is specified
   format=serialization.PrivateFormat.PKCS8,
   encryption_algorithm=serialization.BestAvailableEncryption(password),
)
key_pem_path = Path("./carrier_keys/carrier_private_key.pem")
key_pem_path.write_bytes(key_pem_bytes)
# public
public_key = private_key.public_key()
public_pem_bytes = public_key.public_bytes(
   encoding=serialization.Encoding.PEM,
   format=serialization.PublicFormat.SubjectPublicKeyInfo,
)
public_pem_path = Path("./carrier_keys/carrier_public_key.pem")
public_pem_path.write_bytes(public_pem_bytes)

# C - Generate a public key (.pem) from other client when it is publishing
# We need the public key of the other Client to verify signature
def generateForeignPrimaryKey(nodename, publickey):
    public_pem_bytes = publickey.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    public_pem_path = Path(f"./carrier_keys/{nodename}_public_key.pem")
    public_pem_path.write_bytes(public_pem_bytes)

## Decrypt the fingerprint to know that it can be trusted
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
        return None
    
def verify(signature, message, public_key, token):
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
        if validate_jwt(token) is not True:
          print('Invalid JWT token!')
          return False
        
        print('Valid JWT token!')
        return True
    except InvalidSignature:
        return False
    # "The signature, the message or the Public Key is invalid"

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

# Signs the signature
def sign(message, private_key):
    return private_key.sign(
        message,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )

def on_message(client,userdata,message):
    global current_state
    try:
        data = json.loads(message.payload.decode("utf-8"))
      
        process_incoming_data(data)
    except json.JSONDecodeError:
        print("Failed to decode JSON data.")

def process_incoming_data(datajson):
    global current_state, carrier_tokens
    
    newkeydata = datajson.get("message", None)
    if newkeydata:
        # Decode JSON to encrypted message
        encrypted_fingerprint = base64.b64decode(newkeydata)
        
        # Find carrier private key
        private_pem_bytes = Path("./carrier_keys/carrier_private_key.pem").read_bytes()
        
        # Convert bytes to private key
        carrier_private_key = load_pem_private_key(private_pem_bytes, password=b"carrier_transport")
        
        # Decrypt the message and validate if the fingerprint has a valid message
        decrypted_message = decrypt(encrypted_fingerprint, carrier_private_key)
        if decrypted_message == b'hello carrier':
            print("Fingerprint uses the correct primary key. Handshake Accepted")
            
            # Decode the public key from base64 in the incoming message
            public_pem_bytes_local = base64.b64decode(datajson.get("public_key"))
            
            # Load the local public key from bytes
            try:
                local_public_key = load_pem_public_key(public_pem_bytes_local)
            except Exception as e:
                print(f"Failed to load the public key: {e}")
                return
            
            # Generate the public key file for the other node
            generateForeignPrimaryKey(datajson.get("node_name"), local_public_key)
            print("Success: A new key is added inside the carrier")
        else:
            print("Failed to decrypt the message or the fingerprint is invalid.")
    else:
         # Decrypt the received message
        public_pem_bytes = Path(f"./carrier_keys/{datajson.get('node_name')}_public_key.pem").read_bytes()
        local_public_key = load_pem_public_key(public_pem_bytes)
        signature = base64.b64decode(datajson.get("signature"))
        message_data = base64.b64decode(datajson.get("data"))
        token = datajson.get('token')

        if verify(signature, message_data, local_public_key, token):
            print("Signature is Valid")

            private_pem_bytes = Path("./carrier_keys/carrier_private_key.pem").read_bytes()
            carrier_private_key = load_pem_private_key(private_pem_bytes, password=b"carrier_transport")
            
            # Decrypt the data
            decrypt_data = decrypt(message_data, carrier_private_key)
            if decrypt_data is None:
                print("Failed to decrypt the message.")
                return
            data = json.loads(decrypt_data)
            UPC_ID=datajson["UPC_ID"]
            # Check if UPC_ID exists in the current_state dictionary
            if UPC_ID not in current_state:
                print(f"UPC_ID {UPC_ID} not found.")
                return

            # Check the current state of the provided UPC_ID
            if current_state[UPC_ID]["status"] == 'waiting':
                # Step 3
                current_state[UPC_ID]["status"] = 'origin'
                
                formatted_data = {
                    "UPC_ID": data.get("UPC_ID"),
                    data.get("country"): {
                        "city": data.get("city"),
                        "postalcode": data.get("postalcode"),
                        "province": data.get("province")
                    },
                    "time": data.get("time"),
                    "status": current_state[UPC_ID]["status"]
                }
                response = requests.post(f"{FLASK_API_URL}/{data.get('UPC_ID')}", json={"message": formatted_data, "token": carrier_tokens[UPC_ID]})
                if response.status_code == 201:
                    print("Message added successfully!")
                    publish_message('Step3',data.get('UPC_ID'))
                else:
                    print("Failed to add message:", response.json())
                    
            elif current_state[UPC_ID]["status"] == 'origin':
                # Step 7
                current_state[UPC_ID]["status"] = 'inDestination'
                formatted_data = {
                    "UPC_ID": data.get("UPC_ID"),
                    "doorman": {
                        "client_name": data.get("client_name"),
                        "door_number": data.get("door_number"),
                        "phone_number": data.get("phone_number")
                    },
                    "time": data.get("time"),
                    "status": current_state[UPC_ID]["status"]  
                }
                
                response = requests.post(f"{FLASK_API_URL}/{data.get('UPC_ID')}", json={"message": formatted_data, "token": carrier_tokens[UPC_ID]})
                if response.status_code == 201:
                    print("Message added successfully!")
                    publish_message('Step8',data.get('UPC_ID'))
                else:
                    print("Failed to add message:", response.json())
                    
            elif current_state[UPC_ID]["status"] == 'inDestination':
                # Step 11
                current_state[UPC_ID]["status"] = 'delivered'
                
                formatted_data = {
                    "UPC_ID": data.get("UPC_ID"),
                    "proof": {
                        "image1": "placeholder1",
                        "image2": "placeholder2"
                    },
                    "time": data.get("time"),
                    "status": current_state[UPC_ID]["status"]  
                }
                
                response = requests.post(f"{FLASK_API_URL}/{data.get('UPC_ID')}", json={"message": formatted_data, "token": carrier_tokens[UPC_ID]})
                if response.status_code == 201:
                    print("Message added successfully!")
                else:
                    print("Failed to add message:", response.json())
                
def publish_message(message, UPC_ID):
    global current_state
    """Publishes a message to the MQTT topic."""
    # Encrypt message using local public key
    public_pem_bytes_local = Path("./carrier_keys/local_public_key.pem").read_bytes()
    local_public_key = load_pem_public_key(public_pem_bytes_local)
    # Encode the message string into bytes before encryption
    encrypted_message = encrypt(message.encode('utf-8'), local_public_key)
    # Convert the encrypted message (bytes) to a base64-encoded string
    encrypted_message_base64 = base64.b64encode(encrypted_message).decode('utf-8')
    # Sign the messages
    pre_signature = sign(encrypted_message, private_key)
    signature = base64.b64encode(pre_signature).decode('utf-8')
    # Publish the message to the MQTT topic with base64-encoded encrypted data
    client.publish(send_topic, json.dumps({"UPC_ID": UPC_ID, "data": encrypted_message_base64, "signature": signature}))

# MQTT client setup
client = mqtt.Client(client_id="Client2")
client.username_pw_set(username="testuser", password="pass1")
client.on_message = on_message

if __name__ == "__main__":
    # Connect and subscribe to the MQTT broker
    client.connect(broker_address, port)
    client.subscribe(receive_topic)
    client.loop_start()

    print("--- WAITING FOR NEW ORDER ---")

    try:
        while True:
            pass
    except KeyboardInterrupt:
        client.loop_stop()
        client.disconnect()