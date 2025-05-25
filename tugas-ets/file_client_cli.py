import socket
import json
import base64
import logging
import os 
server_address=('172.16.16.102',6667) # Sesuaikan dengan alamat server Anda

def send_command(command_str=""):
    global server_address
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect(server_address)
        command_to_send = (command_str + "\r\n\r\n").encode() 
        sock.sendall(command_to_send)
        
        data_received=""
        while True:
            data = sock.recv(8192) 
            if data:
                data_received += data.decode()
                if "\r\n\r\n" in data_received:
                    break
            else:
                break

        json_data = data_received.split("\r\n\r\n")[0]
        hasil = json.loads(json_data)
        return hasil
    except json.JSONDecodeError as e:
        logging.error(f"JSON Decode Error: {e} | Raw data: {data_received}")
        print(f"Error: Invalid JSON response from server. Raw: {data_received}")
        return {"status": "ERROR", "data": "Invalid JSON response from server."}
    except Exception as e:
        logging.error(f"Error during data receiving/sending: {e}")
        print(f"Error client: {e}")
        return {"status": "ERROR", "data": f"Client error: {e}"}
    finally:
        sock.close()

def remote_list():
    command_str=f"LIST"
    hasil = send_command(command_str)
    if (hasil['status']=='OK'):
        print("daftar file : ")
        for nmfile in hasil['data']:
            print(f"- {nmfile}")
        return True
    else:
        print(f"Gagal menampilkan daftar file")
        print(f"Respond Server: {hasil['data']}")
        return False

def remote_get(filename=""):
    if not filename:
        print("Gunakan: get <remote_filename>")
        return False
        
    command_str=f"GET {filename}"
    hasil = send_command(command_str)
    if (hasil['status']=='OK'):
        namafile= hasil['data_namafile']
        isifile = base64.b64decode(hasil['data_file'])
        fp = open(namafile,'wb+')
        fp.write(isifile)
        fp.close()
        print(f"File '{namafile}' berhasil diunduh.")
        return True
    else:
        print(f"Gagal mengunduh file '{filename}'")
        print(f"Respond Server: {hasil['data']}")
        return False

def remote_upload(filepath_local="", filename_remote=""):
    if not filepath_local or not filename_remote:
        print("Gunakan: upload <local_filepath> <remote_filename>")
        return False
    
    if not os.path.exists(filepath_local):
        print(f"Error: File lokal '{filepath_local}' tidak ditemukan.")
        return False

    try:
        with open(filepath_local, 'rb') as fp:
            file_content_bytes = fp.read()
        encoded_content = base64.b64encode(file_content_bytes).decode('utf-8')
        command_str = f"UPLOAD {filename_remote} {encoded_content}"
        hasil = send_command(command_str)

        if (hasil['status']=='OK'):
            print(f"Upload '{filepath_local}' ke '{filename_remote}' berhasil")
            print(f"Respond Server: {hasil['data']}")
            return True
        else:
            print(f"Upload '{filepath_local}' ke '{filename_remote}' gagal")
            print(f"Respond Server: {hasil['data']}")
            return False
    except Exception as e:
        print(f"Terjadi kesalahan saat upload: {e}")
        return False

def remote_delete(filename_remote=""):
    if not filename_remote:
        print("Gunakan: delete <remote_filename>")
        return False
    
    command_str = f"DELETE {filename_remote}"
    hasil = send_command(command_str)

    if (hasil['status']=='OK'):
        print(f"File '{filename_remote}' berhasil dihapus")
        print(f"Respond Server: {hasil['data']}")
        return True
    else:
        print(f"Hapus file '{filename_remote}' gagal")
        print(f"Respond Server: {hasil['data']}")
        return False

def main_cli():
    print("FILE CLIENT CLI")
    print("============================================================================")
    print("Perintah yang tersedia:")
    print("  list                           - Menampilkan daftar file di server")
    print("  get <remote_filename>          - Mengunduh file dari server")
    print("  upload <local_filepath> <remote_filename> - Mengunggah file ke server")
    print("  delete <remote_filename>       - Menghapus file di server")
    print("  exit                           - Keluar dari aplikasi")
    print("============================================================================")

    while True:
        try:
            command_line = input(">>> ").strip()
            if not command_line:
                continue

            parts = command_line.split(' ', 1)
            command = parts[0].lower()
            args = parts[1] if len(parts) > 1 else ""

            if command == 'list':
                remote_list()
                print(" ")
            elif command == 'get':
                remote_get(args)
                print(" ")
            elif command == 'upload':
                upload_parts = args.split(' ', 1)
                if len(upload_parts) == 2:
                    remote_upload(upload_parts[0], upload_parts[1])
                    print(" ")
                else:
                    print("Gunakan: upload <local_filepath> <remote_filename>")
                    print(" ")
            elif command == 'delete':
                remote_delete(args)
                print(" ")
            elif command == 'exit':
                print("\nTerima kasih telah menggunakan File Client CLI!")
                break
            else:
                print(f"Perintah '{command}' tidak dikenal.")
                print(" ")
                
        except KeyboardInterrupt:
            print("\n\nProgram dihentikan oleh user.")
            print("Terima kasih telah menggunakan File Client CLI!")
            break
        except Exception as e:
            print(f"Terjadi error: {str(e)}")
            print("Silakan coba lagi.\n")

if __name__=='__main__':
    server_address=('172.16.16.102',6667) # Sesuaikan dengan alamat server Anda
    print("Menghubungkan ke server...")
    print(f"Server: {server_address[0]}:{server_address[1]}\n")
    
    try:
        print("Testing connection...")
        remote_list()
        print("Koneksi berhasil!\n")
        
        main_cli()
        
    except Exception as e:
        print(f"Error connecting to server: {str(e)}")
        print("Pastikan server berjalan dan dapat diakses.")
        print(f"Server address: {server_address[0]}:{server_address[1]}")

    