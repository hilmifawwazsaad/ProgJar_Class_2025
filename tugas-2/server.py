# SERVER.PY
import socket
import threading
import logging
from datetime import datetime

logging.basicConfig(
    format='[%(asctime)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.INFO
)

class ProcessTheClient(threading.Thread):
    def __init__(self, connection, address):
        self.connection = connection
        self.address = address
        threading.Thread.__init__(self)
    
    def run(self):
        logging.info(f"Terhubung dengan {self.address}")
        try:
            while True:
                data = self.connection.recv(256)
                if not data:
                    break
                
                text = data.decode('utf-8').strip()
                logging.info(f"Data diterima dari {self.address}: {text}")
                
                if text.upper() == "TIME":
                    now = datetime.now()
                    waktu = now.strftime("%H:%M:%S")
                    msg = f"JAM {waktu}\r\n"
                    self.connection.sendall(msg.encode('utf-8'))
                    logging.info(f"Mengirim waktu ke {self.address}: JAM {waktu}")
                    
                elif text.upper() == "QUIT":
                    logging.info(f"{self.address} meminta keluar")
                    break
                    
                else:
                    err = "PERINTAH TIDAK VALID\r\n"
                    self.connection.sendall(err.encode('utf-8'))
                    logging.info(f"Perintah tidak dikenal dari {self.address}: {text}")
                    
        except Exception as e:
            logging.error(f"Error dengan {self.address}: {e}")
        finally:
            self.connection.close()
            logging.info(f"Koneksi ditutup dengan {self.address}\n")

class Server(threading.Thread):
    def __init__(self):
        self.the_clients = []
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        threading.Thread.__init__(self)
    
    def run(self):
        host = '0.0.0.0'
        port = 45000
        
        self.my_socket.bind((host, port))
        self.my_socket.listen(5)  # Allow multiple concurrent connections
        logging.info(f"Listening pada {host}:{port}")
        
        while True:
            self.connection, self.client_address = self.my_socket.accept()
            logging.info(f"Koneksi baru dari {self.client_address}")
            
            # Buat thread baru untuk setiap client (multithreading)
            clt = ProcessTheClient(self.connection, self.client_address)
            clt.start()
            self.the_clients.append(clt)

def main():
    svr = Server()
    svr.start()

if __name__ == "__main__":
    main()