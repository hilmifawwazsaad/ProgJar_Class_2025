import socket
import os
import base64
import json
import time
from glob import glob

def parse_response(response_str):
    try:
        header_part, body_part = response_str.split('\r\n\r\n', 1)
        return header_part, body_part
    except ValueError:
        return response_str, ""

def print_response_body(body_str):
    if not body_str.strip():
        print("(Respons kosong)")
        return
        
    try:
        data = json.loads(body_str)
        print(json.dumps(data, indent=4))
    except json.JSONDecodeError:
        print("Raw response:")
        print(body_str[:500])

def print_full_response(response_str):
    try:
        header_part, body_part = response_str.split('\r\n\r\n', 1)
        print(header_part)
        print()
        
        try:
            data = json.loads(body_part)
            print(json.dumps(data, indent=4))
        except json.JSONDecodeError:
            print(body_part)
    except ValueError:
        print(response_str)

def send_request(host, port, request_str, timeout=30):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            sock.connect((host, port))
            
            if isinstance(request_str, str):
                sock.sendall(request_str.encode('utf-8'))
            else:
                sock.sendall(request_str)
            
            response_bytes = b''
            sock.settimeout(5)
            
            while b'\r\n\r\n' not in response_bytes:
                try:
                    data = sock.recv(1024)
                    if not data:
                        break
                    response_bytes += data
                except socket.timeout:
                    break
            
            response_str = response_bytes.decode('utf-8', errors='ignore')
            if 'Content-Length:' in response_str:
                try:
                    header_part, body_part = response_str.split('\r\n\r\n', 1)
                    content_length = 0
                    for line in header_part.split('\r\n'):
                        if line.lower().startswith('content-length:'):
                            content_length = int(line.split(':')[1].strip())
                            break
                    
                    body_bytes = body_part.encode('utf-8')
                    while len(body_bytes) < content_length:
                        try:
                            data = sock.recv(min(4096, content_length - len(body_bytes)))
                            if not data:
                                break
                            body_bytes += data
                        except socket.timeout:
                            break
                    
                    response_bytes = header_part.encode('utf-8') + b'\r\n\r\n' + body_bytes
                    
                except Exception as e:
                    print(f"Error parsing Content-Length: {e}")
            else:
                sock.settimeout(2)
                try:
                    while True:
                        data = sock.recv(4096)
                        if not data:
                            break
                        response_bytes += data
                except socket.timeout:
                    pass
            return response_bytes.decode('utf-8', errors='ignore')
            
    except ConnectionRefusedError:
        return "KONEKSI GAGAL: Pastikan server sudah berjalan."
    except socket.timeout:
        return "TIMEOUT: Server tidak merespons dalam waktu yang ditentukan."
    except Exception as e:
        return f"Terjadi Error: {str(e)}"

def list_files(host, port):
    print("\n[INFO] Meminta daftar file dari server...")
    request = "GET /list HTTP/1.0\r\n\r\n"
    response = send_request(host, port, request, 10)
    header, body = parse_response(response)
    print("=== DAFTAR FILE DI SERVER ===")
    
    try:
        data = json.loads(body)
        if data.get('status') == 'success':
            files = data.get('files', [])
            if files:
                filenames = []
                for i, file_info in enumerate(files, 1):
                    if isinstance(file_info, dict):
                        filename = file_info.get('name', str(file_info))
                        size = file_info.get('size', 'Unknown')
                        print(f"{i}. {filename} ({size} bytes)")
                        filenames.append(filename)
                    else:
                        print(f"{i}. {file_info}")
                        filenames.append(file_info)
                return filenames
            else:
                print("Server kosong, tidak ada file.")
                return []
        else:
            print("Error:", data.get('message', 'Unknown error'))
            return []
    except json.JSONDecodeError:
        print("Error parsing server response:")
        print("Raw response:", body[:200])
        return []

def get_local_files():
    files = []
    files_dir = 'files'
    
    if not os.path.exists(files_dir):
        print(f"Folder '{files_dir}' tidak ditemukan!")
        return files
    
    extensions = ['*.txt', '*.jpg', '*.jpeg', '*.png', '*.pdf', '*.doc', '*.docx']
    for ext in extensions:
        pattern = os.path.join(files_dir, ext)
        files.extend(glob(pattern))
    return files

def show_local_files():
    print("\n=== DAFTAR FILE LOKAL (folder files/) ===")
    files = get_local_files()
    if files:
        for i, filepath in enumerate(files, 1):
            filename = os.path.basename(filepath)
            size = os.path.getsize(filepath)
            print(f"{i}. {filename} ({size} bytes)")
        return files
    else:
        print("Tidak ada file yang ditemukan di folder files/.")
        return []

def upload_file(host, port, filepath):
    if not os.path.exists(filepath):
        print(f"ERROR: File '{filepath}' tidak ditemukan.")
        return
    
    filename = os.path.basename(filepath)
    file_size = os.path.getsize(filepath)
    print(f"[INFO] Mengirim file '{filename}' ({file_size} bytes) ke server...")
    
    try:
        with open(filepath, 'rb') as f:
            file_content_binary = f.read()
        
        print("[INFO] Encoding file ke base64...")
        file_content_base64 = base64.b64encode(file_content_binary).decode('utf-8')
        
        body = file_content_base64
        headers = [
            "POST /upload HTTP/1.0",
            f"X-Filename: {filename}",
            f"Content-Length: {len(body)}",
            "Connection: close"
        ]
        request = "\r\n".join(headers) + "\r\n\r\n" + body
        
        print("[INFO] Mengirim request ke server...")
        timeout = max(60, file_size // 10000)
        response = send_request(host, port, request, timeout)
        
        if "TIMEOUT" in response or "KONEKSI GAGAL" in response or "Terjadi Error" in response:
            print(f"ERROR: {response}")
            return
            
        header, body = parse_response(response)
        print("=== RESPONS SERVER ===")
        print_full_response(response)

    except Exception as e:
        print(f"ERROR: Gagal mengupload file - {str(e)}")

def send_request_binary(host, port, request_str, timeout=30):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            sock.connect((host, port))
            sock.sendall(request_str.encode('utf-8'))
            response_bytes = b''
            sock.settimeout(10)
            
            while b'\r\n\r\n' not in response_bytes:
                try:
                    data = sock.recv(4096)
                    if not data:
                        break
                    response_bytes += data
                except socket.timeout:
                    break
            
            if b'Content-Length:' in response_bytes:
                try:
                    header_end = response_bytes.find(b'\r\n\r\n')
                    header_part = response_bytes[:header_end].decode('utf-8', errors='ignore')
                    body_part = response_bytes[header_end + 4:]
                    
                    content_length = 0
                    for line in header_part.split('\r\n'):
                        if line.lower().startswith('content-length:'):
                            content_length = int(line.split(':')[1].strip())
                            break
                    
                    while len(body_part) < content_length:
                        try:
                            remaining = content_length - len(body_part)
                            data = sock.recv(min(65536, remaining))
                            if not data:
                                break
                            body_part += data
                        except socket.timeout:
                            break
                    response_bytes = response_bytes[:header_end + 4] + body_part
                    
                except Exception as e:
                    print(f"Error parsing Content-Length: {e}")
            else:
                sock.settimeout(5)
                try:
                    while True:
                        data = sock.recv(65536)
                        if not data:
                            break
                        response_bytes += data
                except socket.timeout:
                    pass
            return response_bytes
            
    except ConnectionRefusedError:
        return b"KONEKSI GAGAL: Pastikan server sudah berjalan."
    except socket.timeout:
        return b"TIMEOUT: Server tidak merespons dalam waktu yang ditentukan."
    except Exception as e:
        return f"Terjadi Error: {str(e)}".encode('utf-8')

def download_file(host, port, filename):
    print(f"[INFO] Mengunduh file '{filename}' dari server...")
    request = f"GET /{filename} HTTP/1.0\r\n\r\n"
    response_bytes = send_request_binary(host, port, request, 30)
    
    try:
        header_end = response_bytes.find(b'\r\n\r\n')
        if header_end == -1:
            print("ERROR: Invalid response format")
            return
        
        header_part = response_bytes[:header_end].decode('utf-8', errors='ignore')
        body_part = response_bytes[header_end + 4:]
        
        if "200 OK" in header_part:
            local_filename = f"downloaded_{filename}"
            with open(local_filename, 'wb') as f:
                f.write(body_part)
            file_size = len(body_part)
            print(f"File berhasil diunduh sebagai '{local_filename}' ({file_size} bytes)")
        else:
            print("Error downloading file:")
            try:
                error_body = body_part.decode('utf-8')
                print_response_body(error_body)
            except:
                print("Binary error response")
    except Exception as e:
        print(f"ERROR: Gagal mengunduh file - {str(e)}")

def delete_file(host, port, filename):
    print(f"[INFO] Menghapus file '{filename}' dari server...")
    request = f"DELETE /delete/{filename} HTTP/1.0\r\n\r\n"
    response = send_request(host, port, request, 10)
    header, body = parse_response(response)
    print("=== RESPONS SERVER ===")
    print_full_response(response)

def main():
    TARGET_HOST = '172.16.16.101'
    TARGET_PORT = 8885 
    
    print(f"Terhubung ke server: {TARGET_HOST}:{TARGET_PORT}")
    print("\n" + "="*50)
    print("        FILE TRANSFER CLIENT")
    print("="*50)
    print("1. Lihat file di server")
    print("2. Upload file ke server")
    print("3. Download file dari server")
    print("4. Hapus file dari server")
    print("0. Keluar")
    print("="*50)

    while True:
        try:
            choice = input("\nPilih menu (0-4): ").strip()
            
            if choice == '0':
                print("Terima kasih! Program selesai.")
                break
            elif choice == '1':
                list_files(TARGET_HOST, TARGET_PORT)
            elif choice == '2':
                local_files = show_local_files()
                if local_files:
                    try:
                        file_choice = int(input(f"\nPilih file untuk diupload (1-{len(local_files)}): "))
                        if 1 <= file_choice <= len(local_files):
                            selected_file = local_files[file_choice - 1]
                            upload_file(TARGET_HOST, TARGET_PORT, selected_file)
                        else:
                            print("Pilihan tidak valid!")
                    except ValueError:
                        print("Masukkan angka yang valid!")
                else:
                    print("Pastikan folder 'files/' ada dan berisi file yang ingin diupload.")
            elif choice == '3':
                server_files = list_files(TARGET_HOST, TARGET_PORT)
                if server_files:
                    try:
                        file_choice = int(input(f"\nPilih file untuk didownload (1-{len(server_files)}): "))
                        if 1 <= file_choice <= len(server_files):
                            selected_file = server_files[file_choice - 1]
                            download_file(TARGET_HOST, TARGET_PORT, selected_file)
                        else:
                            print("Pilihan tidak valid!")
                    except ValueError:
                        print("Masukkan angka yang valid!")      
            elif choice == '4':
                server_files = list_files(TARGET_HOST, TARGET_PORT)
                if server_files:
                    try:
                        file_choice = int(input(f"\nPilih file untuk dihapus (1-{len(server_files)}): "))
                        if 1 <= file_choice <= len(server_files):
                            selected_file = server_files[file_choice - 1]
                            confirm = input(f"Yakin ingin menghapus '{selected_file}'? (y/n): ")
                            if confirm.lower() == 'y':
                                delete_file(TARGET_HOST, TARGET_PORT, selected_file)
                            else:
                                print("Penghapusan dibatalkan.")
                        else:
                            print("Pilihan tidak valid!")
                    except ValueError:
                        print("Masukkan angka yang valid!")
            else:
                print("Pilihan tidak valid! Silakan pilih 0-4.")        
        
        except KeyboardInterrupt:
            print("\n\nProgram dihentikan oleh user.")
            break
        except Exception as e:
            print(f"Terjadi error: {str(e)}")
        
        print(" ")
        print("="*50)

if __name__ == '__main__':
    main()