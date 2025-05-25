from socket import *
import socket
import logging
from file_protocol import FileProtocol
import concurrent.futures
import sys

protocol_handler = FileProtocol()

def process_client_request(client_conn, client_addr):
    """Function to handle client requests"""
    logging.warning(f"Processing new client connection from {client_addr}")
    message_buffer = ""
    try:
        # Increase socket timeout for large file transfers
        client_conn.settimeout(1800)  # 30 minutes timeout
        
        # Increase buffer size for better performance
        while True:
            received_data = client_conn.recv(1024*1024)  # 1MB buffer size
            if not received_data:
                break
            message_buffer += received_data.decode()
            while "\r\n\r\n" in message_buffer:
                cmd_string, message_buffer = message_buffer.split("\r\n\r\n", 1)
                processed_result = protocol_handler.proses_string(cmd_string)
                server_response = processed_result + "\r\n\r\n"
                client_conn.sendall(server_response.encode())
    except Exception as e:
        logging.warning(f"Client processing error: {str(e)}")
    finally:
        logging.warning(f"Client connection from {client_addr} has been terminated")
        client_conn.close()

class FileServer:
    def __init__(self, host_ip='0.0.0.0', server_port=8889, worker_pool_size=5):
        self.server_address = (host_ip, server_port)
        self.worker_pool_size = worker_pool_size
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Set socket timeout
        self.server_socket.settimeout(1800)  # 30 minutes timeout    def run(self):
        logging.warning(f"File server is now running on {self.server_address} with thread pool size {self.worker_pool_size}")
        self.server_socket.bind(self.server_address)
        self.server_socket.listen(5)  # Increased backlog
        
        # Create a ThreadPoolExecutor
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.worker_pool_size) as executor:
            try:
                while True:
                    client_connection, client_addr = self.server_socket.accept()
                    logging.warning(f"New client connection established from {client_addr}")
                    
                    # Submit the client handling task to the thread pool
                    executor.submit(process_client_request, client_connection, client_addr)
            except KeyboardInterrupt:
                logging.warning("Server is shutting down gracefully")
            finally:
                if self.server_socket:
                    self.server_socket.close()

def main():
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='File Server with Threading Pool')
    parser.add_argument('--port', type=int, default=6667, help='Server port (default: 6667)')
    parser.add_argument('--pool-size', type=int, default=5, help='Thread pool size (default: 5)')
    args = parser.parse_args()
    
    print(f"Initializing File Server with Thread Pool:")
    print(f"  Binding IP: 0.0.0.0")
    print(f"  Listening Port: {args.port}")
    print(f"  Worker Pool Size: {args.pool_size}")
    print(f"  Use Ctrl+C to terminate the server")
    
    file_server = FileServer(host_ip='0.0.0.0', server_port=args.port, worker_pool_size=args.pool_size)
    try:
        file_server.run()
    except KeyboardInterrupt:
        print("\nShutting down file server gracefully...")

if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')
    main()