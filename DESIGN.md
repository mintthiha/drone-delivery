# Seller and Carrier APIs with MQTT using Docker

# Design

## Architecture and components

#### MQTT Broker

- local_distribution
    - The local distribution represents the _Seller_, the business responsible for giving a package to the buyer. The `local_distribution` and `carrier_transport` work in constant communication for each order, facilitated by a `MQTT broker`, to ensure the successful delivery of the package to the customer. The data exchanged between these two entities is encrypted, and only minimal, necessary information about the client is shared.
- carrier_transport
    - The carrier transport represents the various entities responsible for delivering the package, which can include trucks, drones, or even individuals. The `carrier_transport` continuously updates its status and location, sharing this information with authorized parties who are permitted to view it.
- carrier_transport_with_camera
  - Works the same as carrier_transport but will take a proof picture at the end that will be shown in dashboard, this also will ask the user to scan the QR code between indestination and delivering state to make sure the order is correct and that it will be shipped correctly
- dashboard
    - Using the `MQTT Broker`, the `dashboard` subscribes to the same topic as the `carrier_transport` to track the package's location and display its current status. Additionally, the `dashboard` shows proof of delivery once the `carrier_transport` has successfully reached the final destination.

_Note: These 3 files run in threads, meaning it can simultaneously place orders, deliver them and show proofs for them at the same time!_

#### API

- API_Carrier
  - The `API_Carrier` purpose is to display information about the current status of the `carrier_transport` in `JSON` like form (Accessible using a `GET`). There is also a `POST`, used by the `carrier_transport` to add correct information in the API. There are `JWT_Tokens` to allow only authorized users to `POST` and `GET`.

- API_Seller
  - The `API_Seller` holds the private information of all the orders. Using `Flask`, there are `GET` methods that can fetch the mininal information of a client in order to perform the delivery, which is mentioned later. There are also `JWT Tokens` in use, in order to allow only authorized users to access this data.

- Endpoints_tests
  - Both APIs include Python tests to ensure their functionality remains correct and reliable over time.



##### Step-By-Step Process Of Broker Exchange

1- `local_distribution` fetch GET **/api/order/UPC_ID/country_destination**

2- `local_distribution` sends to `carrier_transport`

3- `carrier_transport` recieves the info and use POST in **/api/shipment/<UPC_ID>**

4- `carrier_transport` tells `local_distribution` that it posted the information

5- `local_distribution` fetch GET **/api/order/UPC_ID/postal_code_destination** 

6- `local_distribution` sends to `carrier_transport`

6.1- `carrier_transport_with_camera.py` if used will ask to scan QR CODE before proceeding

7- `carrier_transport` recieves the info and use POST in **/api/shipment/<UPC_ID>**

8- `carrier_transport` tells `local_distribution` that it posted the information

9- `local_distribution` fetch GET **/api/order/UPC_ID/door_destination**

10- `local_distribution` sends to `carrier_transport`

11-  `carrier_transport_with_camera.py` if used will take proof pictures and put them in dashboard
#### Seller API

`API_Seller`
Seller is a Flask App that has GET routes that are supposed to fetch information from a file `data/shipment_data`. The broker depends on that information.

- Dockerfile
    - Exposes port 5000
    - Executes `pip install -r requirements.txt` inside container
- app.py
    - Flask
        - Runs On Port 5000
    - Routes
        - GET /api/order/<UPC_ID>/country_destination
        - GET /api/order/<UPC_ID>/door_destination
        - GET /api/order/<UPC_ID>/postal_code_destination
#### Carrier API
`API_Carrier`

Carrier is a Flask App that has a POST route that is supposed to be inserted by the carrier_transport.py
- Dockerfile
    - Exposes port 5001
    - Executes `pip install -r requirements.txt` inside container
- app.py
    - Flask
        - Runs On Port 5001
    - Routes
        - GET & POST /api/shipment/<UPC_ID>

## Security and privacy

The app uses two types of scurity features:

  

1. Public/Private Key Encryption and Signing

    - Every client (`carrier_transport and local_distribution`), generate their own pair of keys. Because local_distribution is not connected with the `carrier_transport` client, the app must make a `handshake` that sends over its public key so that the target client could save on its own node (`in this case it saves inside the carrier_keys folder`). Using `local_distrivution client's downloaded pub key`, carrier encrypts all information that is send over the local client with its signature so that the client that recieves the payload could verify the signature and decrypt the information.

    Here is the Process:

    - Every client generates its own pair of keys inside their node folders. (`/carrier_keys` and `/local_keys`)

    - `local` client wants to send the first message to `carrier` with a payload that has an encrypted `local_public_key.pem` using `carrier_public_key.pem` as a way to encrypt.

    - `carrier` recieves the payload and validates if the message could be decrypted with the `carrier_public_key.pem`. If yes, then `carrier` checks if the decrypted payload has a hardcoded message to verify the identity of the sender `if(payload.message=='hello carrier'): pass`.

    - After the successful handshake, `carrier` downloads the provided public key of `local`.

    - To provide a signature, `carrier` sends back to `local` a message containing an encrypted payload that has been `signed`.

    - `local` recieves from `carrier` and proceeds to communicate back to `carrier` with the signature and the encrypted information.

    Further on, this exchange will proceed until processes are stopped.

  
2. JWT

The `JWT Tokens` are used for authorization between many entities in this program. 

- Local_distribution and Carrier_transport
  - After a successful handshake between the two entities, the `local_distribution` generates a `JWT Token` using the order ID. Each time it sends data to the `carrier_transport`, the token is included. The `carrier_transport` then validates the token, and if it is valid, it proceeds with the next steps.

- Local_distribution and API_Seller
  - Whenever the `local_distribution` uses a `GET` request in order to retrieve order details, the payload has a header as well, which is a `JWT Token`. The `API_Seller` returns the correct response if the token is valid.

- Carrier_transport and API_Carrier
  - Whenever the `carrier_transport` `POST` to the `API_Seller`, the header is supplied with a `JWT Token`, making it so only authorized users are able to add content to the API.

- User and API_Carrier
  - An unauthorized user will not not be able to `GET` the carrier status from the API without the correct tokens. This ensures privary, and the users that are able to visualize it will have the necessary permissions.

## Dashboard

- As mentioned before, the `dashboard` displays the states of all the orders that are being delivered by the `carrier_transport` with their appropriate times. The `dashboard` also shows a proof of delivery when the order has been successfully delivered.