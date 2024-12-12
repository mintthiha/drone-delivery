from dash import Dash, html, dcc, Output, Input
import os
import json
import threading
import shutil
import paho.mqtt.client as mqtt
import signal
import sys
from jwt_module import validate_jwt
import base64
broker_address = "localhost"
port = 1883
receive_topic = "dashboard/topic"

# Store the latest message and state
latest_data = {}
current_state = {}
def clearProofsFolder():
    # Define the folder path
    folder_path = './proofs/'
    # Check if the folder exists
    if os.path.exists(folder_path):
        # Delete all contents within the folder
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            try:
                # Check if it's a file or directory
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)  # Remove the file or symlink
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)  # Remove the directory and its contents
            except Exception as e:
                print(f'Failed to delete {file_path}. Reason: {e}')
    else:
        print(f'The folder {folder_path} does not exist')

# MQTT setup
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        client.subscribe(receive_topic)
    else:
        print(f"Failed to connect with result code {rc}")

def on_message(client, userdata, message):
    global latest_data, current_state
    try:
        data = json.loads(message.payload.decode("utf-8"))
        latest_data[data['UPC_ID']] = data

        # print(data['token'])
        # print(validate_jwt(data['token']))
        # print()

        if validate_jwt(data['token']):
          if data['UPC_ID'] not in current_state:
            current_state[data['UPC_ID']] = 'Nothing'
          
          # Iterate through the items in latest_data
          for upc_order_key, upc_order_details in latest_data.items():
              # Access the nested 'data' dictionary
              nested_data = upc_order_details.get('data', {})
              if 'city' in nested_data and ('postalcode' in nested_data or 'postal_code' in nested_data):
                  current_state[upc_order_key] = 'Origin'
              elif 'door_number' in nested_data:
                  current_state[upc_order_key] = 'In Destination!'
              elif 'postalcode' in nested_data or 'postal_code' in nested_data:
                current_state[upc_order_key] = 'Delivered!'
        else:
            print('The token is not valid for order -> ' + data['UPC_ID'])

    except json.JSONDecodeError:
        print('Failed to decode JSON data.')

# Dash app setup
app = Dash(__name__)

app.layout = html.Div([
    html.H1(
        "Real-Time Shipment Tracking",
        style={
            'textAlign': 'center',
            'color': '#4CAF50',
            'fontFamily': 'Arial, sans-serif',
            'marginBottom': '30px',
            'fontSize': '32px'
        }
    ),
    html.Div(id='tables-container'),  # Placeholder for tables
    dcc.Interval(
        id='interval',
        interval=200,  # Update every 0.5 seconds
        n_intervals=0
    )
], style={'padding': '20px', 'backgroundColor': '#f0f0f5'})

# Callback to update the tables dynamically
@app.callback(
    Output('tables-container', 'children'),
    [Input('interval', 'n_intervals')]
)


def update_tables(n):
    global latest_data, current_state

    # Create a list of tables for each UPC_ID
    tables = []
    for upc_id, details in latest_data.items():
        nested_data = details.get('data', {})
        status = current_state.get(upc_id, 'N/A')
        if status !='Delivered!':
            tables.append(
                html.Table([
                    html.Thead(
                        html.Tr([
                            html.Th("UPC_ID"),
                            html.Th("Status"),
                            html.Th("Time")
                        ])
                    ),
                    html.Tbody([
                        html.Tr([
                            html.Td(upc_id),  # UPC_ID
                            html.Td(status),  # Status
                            html.Td(nested_data['time'])
                        ])
                    ])
                ], style={
                    'width': '50%',
                    'margin': '20px auto',
                    'border': '1px solid #ddd',
                    'borderCollapse': 'collapse',
                    'fontFamily': 'Arial, sans-serif',
                    'fontSize': '18px',
                    'backgroundColor': '#f9f9f9',
                    'padding': '8px',
                    'textAlign': 'center',
                    'boxShadow': '0px 4px 8px rgba(0, 0, 0, 0.1)'
                })
            )         
        else:
            try:
                image_filename = f'proofs/{upc_id}.jpg'  
                print(image_filename)
                if image_filename!= None:
                    encoded_image = base64.b64encode(open(image_filename, 'rb').read()).decode('ascii')
                
                    tables.append(
                    html.Table([
                        html.Thead(
                            html.Tr([
                                html.Th("UPC_ID"),
                                html.Th("Status"),
                                html.Th("Time"),
                                html.Th("Proof")  # Added column header for the proof image
                            ])
                        ),
                        html.Tbody([
                            html.Tr([
                                html.Td(upc_id),  # UPC_ID
                                html.Td(status),  # Status
                                html.Td(nested_data['time']),
                                html.Img(src='data:image/png;base64,{}'.format(encoded_image), style={'width': '50%'}),  # Image shown directly instead of a link
                            ])
                        ])
                    ], style={
                        'width': '50%',
                        'margin': '20px auto',
                        'border': '1px solid #ddd',
                        'borderCollapse': 'collapse',
                        'fontFamily': 'Arial, sans-serif',
                        'fontSize': '18px',
                        'backgroundColor': '#f9f9f9',
                        'padding': '8px',
                        'textAlign': 'center',
                        'boxShadow': '0px 4px 8px rgba(0, 0, 0, 0.1)'
                    })
                    )
            except :
                tables.append(
                    html.Table([
                        html.Thead(
                            html.Tr([
                                html.Th("UPC_ID"),
                                html.Th("Status"),
                                html.Th("Time")
                            ])
                        ),
                        html.Tbody([
                            html.Tr([
                                html.Td(upc_id),  # UPC_ID
                                html.Td("Waiting for proof picture"),  # Status
                                html.Td(nested_data['time'])

                            ])
                        ])
                    ], style={
                        'width': '50%',
                        'margin': '20px auto',
                        'border': '1px solid #ddd',
                        'borderCollapse': 'collapse',
                        'fontFamily': 'Arial, sans-serif',
                        'fontSize': '18px',
                        'backgroundColor': '#f9f9f9',
                        'padding': '8px',
                        'textAlign': 'center',
                        'boxShadow': '0px 4px 8px rgba(0, 0, 0, 0.1)'
                    })
                    )
            
    
    return tables

def signal_handler(sig, frame):
    """Handle Ctrl+C to stop the MQTT client and exit the program gracefully."""
    print("Shutting down gracefully...")
    client.loop_stop()  # Stop the MQTT client loop
    client.disconnect()  # Disconnect the MQTT client
    sys.exit(0)

# Register the signal handler for Ctrl+C
signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
    client = mqtt.Client(client_id="DashboardTest")
    client.username_pw_set(username="dashboard", password="pass1")
    client.connect("localhost", 1883)
    client.loop_start()  # Non-blocking loop
    clearProofsFolder()
    client.on_connect = on_connect
    client.on_message = on_message

    try:
      app.run_server(debug=True, use_reloader = False)
    except KeyboardInterrupt:
        client.loop_stop()  # Stop the MQTT loop
        client.disconnect()  # Disconnect from the MQTT broker