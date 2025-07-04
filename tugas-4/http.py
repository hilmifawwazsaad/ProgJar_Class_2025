import sys
import os
import os.path
import uuid
import json
import base64
from glob import glob
from datetime import datetime

class HttpServer:
    def __init__(self):
        self.sessions = {}
        self.types = {}
        self.types['.pdf'] = 'application/pdf'
        self.types['.jpg'] = 'image/jpeg'
        self.types['.jpeg'] = 'image/jpeg'
        self.types['.png'] = 'image/png'
        self.types['.txt'] = 'text/plain'
        self.types['.html'] = 'text/html'
        self.types['.css'] = 'text/css'
        self.types['.js'] = 'application/javascript'
        self.types['.json'] = 'application/json'
        
        self.upload_dir = 'public'
        if not os.path.exists(self.upload_dir):
            os.makedirs(self.upload_dir)

    def response(self, kode=404, message='Not Found', messagebody=bytes(), headers={}):
        tanggal = datetime.now().strftime('%c')
        resp = []
        resp.append(f"HTTP/1.0 {kode} {message}\r\n")
        resp.append(f"Date: {tanggal}\r\n")
        resp.append("Connection: close\r\n")
        resp.append("Server: myserver/1.0\r\n")
        
        if isinstance(messagebody, str) and messagebody.startswith('{'):
            headers['Content-Type'] = 'application/json'
            
        resp.append(f"Content-Length: {len(messagebody)}\r\n")
        for kk in headers:
            resp.append(f"{kk}:{headers[kk]}\r\n")
        resp.append("\r\n")

        response_headers = "".join(resp)

        if not isinstance(messagebody, bytes):
            messagebody = messagebody.encode()

        response = response_headers.encode() + messagebody
        return response

    def proses(self, data):
        requests = data.split("\r\n")
        baris = requests[0]

        headers = {}
        body_start_index = -1
        for i, line in enumerate(requests[1:]):
            if line == "":
                body_start_index = i + 2
                break
            parts = line.split(":", 1)
            if len(parts) == 2:
                headers[parts[0].strip()] = parts[1].strip()

        body = ""
        if body_start_index != -1:
            body = "\r\n".join(requests[body_start_index:])

        j = baris.split(" ")
        try:
            method = j[0].upper().strip()
            object_address = j[1].strip()

            if method == 'GET':
                return self.http_get(object_address, headers)
            elif method == 'POST':
                return self.http_post(object_address, headers, body)
            elif method == 'DELETE':
                return self.http_delete(object_address, headers)
            else:
                return self.response(405, 'Method Not Allowed', 
                    json.dumps({"status": "error", "message": "Unsupported method"}), {})
        except IndexError:
            return self.response(400, 'Bad Request', 
                json.dumps({"status": "error", "message": "Malformed request"}), {})

    def http_get(self, object_address, headers):
        if object_address == '/list':
            try:
                files = []
                for filename in os.listdir(self.upload_dir):
                    file_path = os.path.join(self.upload_dir, filename)
                    if os.path.isfile(file_path):
                        file_info = {
                            "name": filename,
                            "size": os.path.getsize(file_path),
                            "modified": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                        }
                        files.append(file_info)
                
                response_data = json.dumps({
                    "status": "success", 
                    "files": files,
                    "count": len(files)
                }, indent=2)
                return self.response(200, 'OK', response_data, {})
            except FileNotFoundError:
                response_data = json.dumps({"status": "error", "message": "Directory not found"})
                return self.response(404, 'Not Found', response_data, {})
            except Exception as e:
                response_data = json.dumps({"status": "error", "message": f"Error listing files: {str(e)}"})
                return self.response(500, 'Internal Server Error', response_data, {})

        if object_address.startswith('/download/'):
            filename = object_address.split('/')[-1]
            file_path = os.path.join(self.upload_dir, filename)
            
            if os.path.exists(file_path) and os.path.isfile(file_path):
                try:
                    with open(file_path, 'rb') as fp:
                        isi = fp.read()
                    fext = os.path.splitext(file_path)[1]
                    content_type = self.types.get(fext, 'application/octet-stream')
                    headers_response = {
                        'Content-Type': content_type,
                        'Content-Disposition': f'attachment; filename="{filename}"'
                    }
                    return self.response(200, 'OK', isi, headers_response)
                except Exception as e:
                    response_data = json.dumps({"status": "error", "message": f"Error reading file: {str(e)}"})
                    return self.response(500, 'Internal Server Error', response_data, {})
            else:
                response_data = json.dumps({"status": "error", "message": "File not found"})
                return self.response(404, 'Not Found', response_data, {})

        if object_address == '/':
            response_data = json.dumps({
                "status": "success",
                "message": "Welcome to File Server API",
                "endpoints": {
                    "GET /list": "List all files",
                    "GET /download/{filename}": "Download file",
                    "POST /upload": "Upload file (base64 encoded, X-Filename header required)",
                    "DELETE /delete/{filename}": "Delete file"
                }
            }, indent=2)
            return self.response(200, 'OK', response_data, {})
        
        file_path = os.path.join(self.upload_dir, object_address.strip('/'))
        if os.path.exists(file_path) and os.path.isfile(file_path):
            try:
                with open(file_path, 'rb') as fp:
                    isi = fp.read()
                fext = os.path.splitext(file_path)[1]
                content_type = self.types.get(fext, 'application/octet-stream')
                headers_response = {'Content-Type': content_type}
                return self.response(200, 'OK', isi, headers_response)
            except Exception as e:
                response_data = json.dumps({"status": "error", "message": f"Error reading file: {str(e)}"})
                return self.response(500, 'Internal Server Error', response_data, {})
        
        response_data = json.dumps({"status": "error", "message": "File or endpoint not found"})
        return self.response(404, 'Not Found', response_data, {})

    def http_post(self, object_address, headers, body):
        if object_address != '/upload':
            response_data = json.dumps({"status": "error", "message": "Endpoint not found for POST"})
            return self.response(404, 'Not Found', response_data, {})

        try:
            filename = headers.get('X-Filename')
            if not filename:
                response_data = json.dumps({"status": "error", "message": "X-Filename header is required"})
                return self.response(400, 'Bad Request', response_data, {})

            try:
                file_content = base64.b64decode(body.strip())
            except Exception as e:
                response_data = json.dumps({"status": "error", "message": f"Invalid base64 content: {str(e)}"})
                return self.response(400, 'Bad Request', response_data, {})
            
            file_path = os.path.join(self.upload_dir, filename)
            
            if os.path.exists(file_path):
                response_data = json.dumps({
                    "status": "warning", 
                    "message": f"File '{filename}' already exists and will be overwritten"
                })
                
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            response_data = json.dumps({
                "status": "success", 
                "message": f"File '{filename}' berhasil diupload",
                "filename": filename,
                "size": len(file_content),
                "path": f"/download/{filename}"
            })
            return self.response(201, 'Created', response_data, {})
            
        except Exception as e:
            response_data = json.dumps({"status": "error", "message": f"Upload failed: {str(e)}"})
            return self.response(500, 'Internal Server Error', response_data, {})

    def http_delete(self, object_address, headers):
        if not object_address.startswith('/delete/'):
            response_data = json.dumps({"status": "error", "message": "Invalid DELETE endpoint format. Use /delete/{filename}"})
            return self.response(400, 'Bad Request', response_data, {})

        filename = object_address.split('/')[-1]
        if not filename:
            response_data = json.dumps({"status": "error", "message": "Filename not specified"})
            return self.response(400, 'Bad Request', response_data, {})

        file_path = os.path.join(self.upload_dir, filename)

        try:
            if not os.path.exists(file_path):
                response_data = json.dumps({"status": "error", "message": f"File '{filename}' tidak ditemukan"})
                return self.response(404, 'Not Found', response_data, {})
            
            if not os.path.isfile(file_path):
                response_data = json.dumps({"status": "error", "message": f"'{filename}' is not a file"})
                return self.response(400, 'Bad Request', response_data, {})
            
            os.remove(file_path)
            response_data = json.dumps({
                "status": "success", 
                "message": f"File '{filename}' berhasil dihapus",
                "filename": filename
            })
            return self.response(200, 'OK', response_data, {})
            
        except PermissionError:
            response_data = json.dumps({"status": "error", "message": f"Permission denied: cannot delete '{filename}'"})
            return self.response(403, 'Forbidden', response_data, {})
        except Exception as e:
            response_data = json.dumps({"status": "error", "message": f"Error deleting file: {str(e)}"})
            return self.response(500, 'Internal Server Error', response_data, {})


def test_server():
    """Function untuk testing server"""
    httpserver = HttpServer()
    
    print("=== Testing HTTP Server ===")
    print("\n1. Testing root endpoint...")
    response = httpserver.proses('GET / HTTP/1.0\r\n\r\n')
    print("Response status: ", response.decode().split('\n')[0])
    
    print("\n2. Testing file listing...")
    response = httpserver.proses('GET /list HTTP/1.0\r\n\r\n')
    print("List response status: ", response.decode().split('\n')[0])
    
    print("\n3. Testing file upload...")
    test_content = "Hello, World! This is a test file."
    encoded_content = base64.b64encode(test_content.encode()).decode()
    upload_request = f'POST /upload HTTP/1.0\r\nX-Filename: test.txt\r\n\r\n{encoded_content}'
    response = httpserver.proses(upload_request)
    print("Upload response status: ", response.decode().split('\n')[0])
    
    print("\n4. Testing file listing after upload...")
    response = httpserver.proses('GET /list HTTP/1.0\r\n\r\n')
    print("List response status: ", response.decode().split('\n')[0])
    
    print("\n5. Testing file download...")
    response = httpserver.proses('GET /download/test.txt HTTP/1.0\r\n\r\n')
    print("Download response status: ", response.decode().split('\n')[0])
    
    print("\n6. Testing file deletion...")
    response = httpserver.proses('DELETE /delete/test.txt HTTP/1.0\r\n\r\n')
    print("Delete response status: ", response.decode().split('\n')[0])
    
    print("\n=== Testing completed ===")
    print("\nAvailable API endpoints:")
    print("GET /             - API information")
    print("GET /list         - List all files")
    print("GET /download/{filename} - Download file")
    print("POST /upload      - Upload file (base64 + X-Filename header)")
    print("DELETE /delete/{filename} - Delete file")

if __name__ == "__main__":
    test_server()