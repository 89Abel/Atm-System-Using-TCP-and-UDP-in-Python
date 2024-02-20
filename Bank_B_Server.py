import socket
import threading
import hashlib
from pymongo import MongoClient

# MongoDB connection for the other bank
client_other_bank = MongoClient('mongodb://localhost:27017/')  # Change the port if needed
db_other_bank = client_other_bank['Bank_B']
collection_name = db_other_bank['Users']

# Function to change the password to hash
def get_hashed_password(password):
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    return hashed_password

# List of user to be inserted to the local bank database
user_data = [
    {"username": "Abebe", "password": "00000", "balance": "12,000 Birr"},
    {"username": "Kebede", "password": "11111", "balance": "13,000 Birr"},
    {"username": "Alemu", "password": "22222", "balance": "14,000 Birr"}
]

# Insert hashed passwords into local bank database
for user_data in user_data:
    user_document = {
        "username": user_data["username"],
        "password": get_hashed_password(user_data["password"]),
        "balance": user_data["balance"]
    }
    collection_name.insert_one(user_document)


# Function to accept and handle request from the atm
def handle_udp():
    # Create a UDP socket for the local atm
    udp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_server_socket.bind(('localhost', 1000))
    print("Bank B Server is listening for UDP connections...")

    while True:
        data, client_address = udp_server_socket.recvfrom(1024)
        # Extract username and password from the received data
        username, password = data.decode().split()
        print(f"Received request from ATM client: {client_address}")
        # Call get_hashed_password to retrieve the hashed password from database
        hashed_password = get_hashed_password(password)
        # Check if the username and password are correct in the local bank
        collection_name = 'Users' # Collection Name
        # Query from atm to check on the local bank database
        user_data_local = db_other_bank[collection_name].find_one({"username": username, "password": hashed_password})

        if user_data_local:
            balance = user_data_local.get("balance", "N/A")
            response = f"Local Bank B - Balance: {balance}"
        elif user_data_local is None:
            # If the username and password is none in the local bank send to other bank
            tcp_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                # Send username and password and receive the result
                tcp_client_socket.connect(('localhost', 6000))
                tcp_client_socket.send(f"{username} {password}".encode())
                new_response = tcp_client_socket.recv(1024).decode()
                response = f"{new_response}"
            finally:
                tcp_client_socket.close()
        else:
            # Print this if the username and password is incorrect in both local and other bank Databases
            response = "Invalid username or password Ok"
        # Send the response to the atm
        udp_server_socket.sendto(response.encode(), client_address)

# Create a function to receive and sent resquest from the other bank
def handle_tcp():
    # MongoDB connection for the local bank
    client_local_bank = MongoClient('mongodb://localhost:27017/')
    db_other_bank = client_local_bank['Bank_B']

    # Create a TCP connection to handle request from the other bank
    tcp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_server_socket.bind(('localhost', 5000))
    tcp_server_socket.listen(5)

    print("Other Bank B Server is listening for TCP connections...")
    while True:

        conn, addr = tcp_server_socket.accept()
        data = conn.recv(1024).decode()
        print(f"Received request from ATM client: {addr}")
        # Extract username and password from the received data
        username, password = data.split()
        collection_name = 'Users'
        client_local_bank = MongoClient('mongodb://localhost:27017/')
        db_other_bank = client_local_bank['Bank_B']
        # Call get_hashed_password to retrieve the hashed password from database
        hashed_password = get_hashed_password(password)
        # Query from other bank to check on the local bank database
        user_data_other_bank = db_other_bank[collection_name].find_one({"username": username, "password": hashed_password})
        if user_data_other_bank:
            balance = user_data_other_bank.get("balance", "N/A")
            balance_response = f"Balance from Other Bank B: {balance}"
        else:
            balance_response = "Invalid username or password"
        # Send the response to the other bank
        conn.send(balance_response.encode())
        conn.close()


if __name__ == "__main__":
    # Use threading to handle the client request concurrently
    tcp_server_thread = threading.Thread(target=handle_tcp)
    udp_server_thread = threading.Thread(target=handle_udp)

    tcp_server_thread.start()
    udp_server_thread.start()

    tcp_server_thread.join()
    udp_server_thread.join
