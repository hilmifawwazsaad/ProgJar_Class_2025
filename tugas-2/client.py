import socket
import logging
import time

IP_SERVER = '172.16.16.101'
PORT_SERVER = 45000

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def send_data():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_ip = "UNKNOWN"

    logging.info("[CLIENT] Membuka koneksi ke server...")
    
    try:
        sock.connect((IP_SERVER, PORT_SERVER))
        client_ip, client_port = sock.getsockname()
        
        logging.info(f"[{client_ip}] Terkoneksi ke {IP_SERVER}:{PORT_SERVER}")
        logging.info(f"[{client_ip}] Menggunakan IP lokal: {client_ip}:{client_port}")
        
        input_time = "TIME\r\n"
        logging.info(f"[{client_ip}] Mengirim ke {IP_SERVER}: {input_time.strip()}")
        sock.sendall(input_time.encode('utf-8'))
        
        response = sock.recv(256)
        logging.info(f"[{IP_SERVER}] Respon ke {client_ip}: {response.decode('utf-8', errors='ignore').strip()}")
        
        input_quit = "QUIT\r\n"
        logging.info(f"[{client_ip}] Mengirim ke {IP_SERVER}: {input_quit.strip()}")
        sock.sendall(input_quit.encode('utf-8'))
        
    except socket.error as err:
        logging.error(f"[{client_ip}] Gagal konekski: {err}")
    finally:
        logging.info(f"[{client_ip}] Menutup koneksi")
        print()
        sock.close()

if __name__ == '__main__':
    while True:
        send_data()
        time.sleep(1) 