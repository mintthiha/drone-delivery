# Descriptive Title

## Overview/Description
This application is a logistics and shipment tracking system that uses a Flask API to handle shipment data and interact with publisher and subscriber services via MQTT for communication. The system tracks the shipment status using unique UPC IDs and integrates dynamic data updates for carriers, customers, and logistics managers.

![System Overview](path/to/screenshot.png)  

## Features of the Application
- **GET /api/shipment/<UPC_ID>**  
  Retrieves the shipment details associated with a specific UPC ID.
  
- **GET /api/order/<UPC_ID>/country_destination**  
  Retrieves the destination country for a specific order.
  
- **GET /api/order/<UPC_ID>/postal_code_destination**  
  Retrieves the destination postal code for a specific order.
  
- **GET /api/order/<UPC_ID>/door_destination**  
  Retrieves the destination door details (door number, client name, phone) for a specific order.

## Design
This application follows a modular design with the following components:
- **Flask API**: Handles HTTP requests and communicates with the database.
- **Publisher**: Sends shipment data updates to the system.
- **Subscriber**: Receives and processes updates sent by the publisher via MQTT.

![Design Diagram](path/to/design-diagram.png)  


## Setup (How to Install and Run)
1. **Start the Docker App**  
   Ensure Docker is installed and running on your machine.

2. **Run Docker Compose**  
   Execute the following from root to bring up the services:
   ```bash
   docker compose up -d
   ```

3. **Run the Python Environment**
  Install the python virtual environment:
  ```bash
  python -m venv .venv
  . ./.venv/Sripts/activate
  pip install -r ./requirements.txt
  ```

4. **Run app**
    make sure Docaker is running
   ```bash
   cd broker
   py dashboard.py
   py carrier_transport.py
   py local_distribution.py
   ```

5. **Run app USING RPI CAMERA AND QR CODE**
    make sure Docker is running
    if permissions are denied run commands using sudo
   ```bash
   cd broker
   python carrier_transport_with_camera.py
   python dashboard.py
   py local_distribution.py
   ```
6. **Run tests (Optional)**
    ```bash
    cd ./API_Carrier
    python -m pytest endpoints_tests.py
    cd ../API_Seller
    python -m pytest endpoints_tests.py
    ```