# Hardcoded data for a single buyer with three shipments
from datetime import datetime

shipments = {
    "UPC_1": {
        "Label_ID": "ID_1",
        "client_info": {
            "product_id": "P_12345",
            "name": "Victor Ponce",
            "phone": "5141234560",
            "destination": {
                "country": "Canada",
                "province": "Quebec",
                "city": "Montreal",
                "postal_code": "H3A 1A1",
                "latitude": 45.5017,
                "longitude": -73.5673,
                "door": "1007"
            }
        },
        "locations": ["origin", "carrier_network", "local_distribution", "final_destination"]
    },
    # Additional shipments (UPC_2, UPC_3) can be added here as needed
}

def get_shipment_data(upc, info_type):
    order = shipments.get(upc)
    if not order:
        return None

    # Return selective data based on info_type
    destination = order["client_info"]["destination"]

    if info_type == "country":
        return destination["country"]
    elif info_type == "province":
        return destination["province"]
    elif info_type == "city":
        return destination["city"]
    elif info_type == "postal_code":
        return destination["postal_code"]
    elif info_type == "latitude":
        return destination["latitude"]
    elif info_type == "longitude":
        return destination["longitude"]
    elif info_type == "door":
        destination["door"]
    elif info_type == "name":
        return order["client_info"]["name"]
    elif info_type == "phone":
        return order["client_info"]["phone"]

    return None