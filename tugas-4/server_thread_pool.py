from socket import *
import socket
import time
import sys
import logging
import multiprocessing
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from http import HttpServer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(threadName)s - %(levelname)s - %(message)s'
)

httpserver = HttpServer()

def ProcessTheClient(connection, address):
    try:
        logging.info(f"Connection from {address} handled by {threading.current_thread().name}")
        
        connection.settimeout(120) 
        request_data = b''
        headers_complete = False
        content_length = 0
        
        # Phase 1: Baca headers dulu
        while not headers_complete:
            try:
                chunk = connection.recv(4096)
                if not chunk:
                    logging.warning(f"No data received from {address}")
                    return
                request_data += chunk
                
                if b'\r\n\r\n' in request_data:
                    headers_complete = True
                    
                    try:
                        header_part = request_data.split(b'\r\n\r\n')[0].decode('utf-8', errors='ignore')
                        for line in header_part.split('\r\n'):
                            if line.lower().startswith('content-length:'):
                                content_length = int(line.split(':')[1].strip())
                                logging.info(f"Content-Length detected: {content_length} bytes")
                                break
                    except Exception as e:
                        logging.error(f"Error parsing Content-Length: {e}")
                
                if len(request_data) > 50000 and not headers_complete:
                    logging.error(f"Headers too large from {address}")
                    connection.close()
                    return
                    
            except socket.timeout:
                logging.error(f"Timeout reading headers from {address}")
                connection.close()
                return
            except Exception as e:
                logging.error(f"Error reading headers from {address}: {e}")
                connection.close()
                return
        
        # Phase 2: Baca body jika ada Content-Length
        if content_length > 0:
            max_file_size = 50 * 1024 * 1024
            if content_length > max_file_size:
                logging.error(f"File too large: {content_length} bytes from {address}")
                error_response = b"HTTP/1.0 413 Payload Too Large\r\nConnection: close\r\n\r\nFile too large"
                connection.sendall(error_response)
                connection.close()
                return
            
            header_end = request_data.find(b'\r\n\r\n') + 4
            current_body = request_data[header_end:]
            bytes_needed = content_length - len(current_body)
            
            logging.info(f"Reading body: {len(current_body)}/{content_length} bytes")
            
            while bytes_needed > 0:
                try:
                    buffer_size = min(65536, bytes_needed)
                    chunk = connection.recv(buffer_size)
                    
                    if not chunk:
                        logging.error(f"Connection closed while reading body from {address}")
                        connection.close()
                        return
                    
                    request_data += chunk
                    bytes_needed -= len(chunk)
                    
                    if content_length > 100000:
                        progress = ((content_length - bytes_needed) / content_length) * 100
                        if int(progress) % 20 == 0:
                            logging.info(f"Upload progress from {address}: {progress:.1f}%")
                    
                except socket.timeout:
                    logging.error(f"Timeout reading body from {address}")
                    connection.close()
                    return
                except Exception as e:
                    logging.error(f"Error reading body from {address}: {e}")
                    connection.close()
                    return
        
        # Phase 3: Process request=
        try:
            rcv = request_data.decode('utf-8', errors='ignore') 
            logging.info(f"Processing request from {address} ({len(rcv)} chars)")
            
            hasil = httpserver.proses(rcv)
            logging.info(f"Response ready: {len(hasil)} bytes")
            
            connection.sendall(hasil)
            logging.info(f"Response sent successfully to {address}")
            
        except Exception as e:
            logging.error(f"Error processing request from {address}: {e}")
            error_response = b"HTTP/1.0 500 Internal Server Error\r\nConnection: close\r\n\r\nServer Error"
            try:
                connection.sendall(error_response)
            except:
                pass
    
    except Exception as e:
        logging.error(f"Fatal error handling {address}: {e}")
    
    finally:
        try:
            connection.close()
        except:
            pass
        
        logging.info(f"Connection {address} closed")
    
    return

def Server():
    the_clients = []
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    port = 8885
    my_socket.bind(('0.0.0.0', port))
    my_socket.listen(50)
    
    print(f"Thread Pool Server running on port {port}")
    
    with ThreadPoolExecutor(20) as executor:
        while True:
            try:
                connection, client_address = my_socket.accept()
                logging.info(f"connection from {client_address}")
                p = executor.submit(ProcessTheClient, connection, client_address)
                the_clients.append(p)
                
                the_clients = [client for client in the_clients if client.running()]
                jumlah = ['x' for i in the_clients if i.running() == True]
                if len(jumlah) > 0:
                    print(f"Active threads: {len(jumlah)} | Time: {datetime.now().strftime('%H:%M:%S')}")
                    
            except KeyboardInterrupt:
                print("\nServer shutdown requested...")
                break
            except Exception as e:
                logging.error(f"Error accepting connection: {e}")

def main():
    try:
        print("="*60)
        print("HTTP Server with ThreadPoolExecutor")
        print("="*60)
        Server()
    except KeyboardInterrupt:
        print("Server stopped by user")
    except Exception as e:
        logging.error(f"Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()