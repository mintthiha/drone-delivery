import time
import jwt
print(jwt.__file__)

# Secret key for signing JWT tokens
SECRET_KEY = "mysecret"

# Function to generate a JWT token
def generate_jwt(upc_id):
    payload = {
        'UPC_ID': upc_id,  # Drone identifier passed as a parameter
        'exp': time.time() + 120  # Token expires in 2 minutes
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token

# Function to validate a JWT token
def validate_jwt(token):
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        upc_id = decoded['UPC_ID']
        # Check token expiration
        if decoded['exp'] < time.time():
            print("Token has expired.")
            return False
        return True
    except jwt.ExpiredSignatureError:
        print("\nSignature has expired.")
        return False
    except jwt.InvalidTokenError:
        print("\nInvalid token.")
        return False

if __name__ == '__main__':
    token = generate_jwt('apple')
    print(f"Generated token: {token}")
    print(f"Token validation: {validate_jwt(token)}")
    time.sleep(121)
    print(f"Token validation: {validate_jwt(token)}")