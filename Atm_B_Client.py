import socket
import getpass

def atm_client(username, password):
    # Create a UDP socket for local operations
    udp_client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Send username and password to the local bank server
    udp_client_socket.sendto(f"{username} {password}".encode(), ('localhost', 1000))

    # Receive the response from the local bank server
    response, _ = udp_client_socket.recvfrom(1024)
    print(response.decode())

    # Close the UDP socket
    udp_client_socket.close()

if __name__ == "__main__":
    # Get user input for username and password
    input_username = input("Enter username: ")
    input_password = getpass.getpass("Enter password: ")

    # Call the ATM client function
    atm_client(input_username, input_password)
