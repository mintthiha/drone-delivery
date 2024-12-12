from flask import Flask, render_template, jsonify, request
from datetime import datetime,timezone
from data.shipment_data import shipments
from jwt_module import validate_jwt

import pytz
app = Flask(__name__)

messages = {}
shipment_data = {
    "UPC_1": {
        "country": "Canada",
        "province": "Ontario",
        "city": "Toronto",
        "door": "1007",
        "clientname": "Victor Ponce",
        "clientphone": "5141234560",
        "postalCode": "M5A 1A1"
    },
    "UPC_2": {
        "country": "USA",
        "province": "California",
        "city": "San Francisco",
        "door": "101",
        "clientname": "John Doe",
        "clientphone": "4151234567",
        "postalCode": "94107"
    },
    "UPC_3": {
        "country": "Mexico",
        "province": "CDMX",
        "city": "Mexico City",
        "door": "202",
        "clientname": "Maria Lopez",
        "clientphone": "5551234567",
        "postalCode": "01010"
    }
}
@app.route('/api/order/<UPC_ID>/country_destination', methods=['GET'])
def get_country_destination(UPC_ID):
    token = request.headers.get("Authorization")

    if not token:
        return jsonify({"error": "Missing authorization token"}), 401

    # Validate the token
    if not validate_jwt(token):
        return jsonify({"error": "Invalid or expired token"}), 403
    
    if UPC_ID in shipment_data:
        data = shipment_data[UPC_ID]
        response = {
            "UPC_ID": UPC_ID,
            "country": data["country"],
            "province": data["province"],
            "city": data["city"],
            "time":  datetime.now(pytz.utc).astimezone(pytz.timezone('US/Eastern')).strftime('%Y-%m-%d %H:%M:%S')
        }
        return jsonify(response), 200
    else:
        return jsonify({"error": "UPC_ID not found"}), 404
    
    

@app.route('/api/order/<UPC_ID>/postalcode_destination', methods=['GET'])
def get_postalcode_destination(UPC_ID):
    token = request.headers.get("Authorization")

    if not token:
        return jsonify({"error": "Missing authorization token"}), 401

    # Validate the token
    if not validate_jwt(token):
        return jsonify({"error": "Invalid or expired token"}), 403
    
    if UPC_ID in shipment_data:
        data = shipment_data[UPC_ID]
        response = {
            "UPC_ID": UPC_ID,
            "postal_code": data["postalCode"],
            "time":  datetime.now(pytz.utc).astimezone(pytz.timezone('US/Eastern')).strftime('%Y-%m-%d %H:%M:%S')
        }
        return jsonify(response), 200
    else:
        return jsonify({"error": "UPC_ID not found"}), 404


@app.route('/api/order/<UPC_ID>/door_destination', methods=['GET'])
def get_door_destination(UPC_ID):
    token = request.headers.get("Authorization")

    if not token:
        return jsonify({"error": "Missing authorization token"}), 401

    # Validate the token
    if not validate_jwt(token):
        return jsonify({"error": "Invalid or expired token"}), 403
    
    if UPC_ID in shipment_data:
        data = shipment_data[UPC_ID]
        response = {
            "UPC_ID": UPC_ID,
            "client_name": data["clientname"],
            "door_number": data["door"],
            "phone_number": data["clientphone"],
            "time":  datetime.now(pytz.utc).astimezone(pytz.timezone('US/Eastern')).strftime('%Y-%m-%d %H:%M:%S')
        }
        return jsonify(response), 200
    else:
        return jsonify({"error": "UPC_ID not found"}), 404

if __name__ == '__main__':
    app.run(debug=True)