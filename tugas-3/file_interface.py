import os
import json
import base64
from glob import glob

class FileInterface:
    def __init__(self):
        os.chdir('files/')

    def list(self,params=[]):
        try:
            filelist = glob('*.*')
            return dict(status='OK',data=filelist)
        except Exception as e:
            return dict(status='ERROR',data=str(e))

    def get(self,params=[]):
        try:
            filename = params[0]
            if (filename == ''):
                return None
            fp = open(f"{filename}",'rb')
            isifile = base64.b64encode(fp.read()).decode()
            return dict(status='OK',data_namafile=filename,data_file=isifile)
        except Exception as e:
            return dict(status='ERROR',data=str(e))

    def upload(self, params=[]):
        try:
            if len(params) < 2:
                return dict(status='ERROR', data='Parameter tidak lengkap. Dibutuhkan nama file dan data base64')
            
            filename = params[0]
            encoded_content = params[1]
            
            if not filename:
                return dict(status='ERROR', data='Parameter filename file tidak boleh kosong')
            if not encoded_content:
                return dict(status='ERROR', data='Parameter content file tidak boleh kosong')
            decoded_content = base64.b64decode(encoded_content)
            with open(f"{filename}", 'wb+') as fp:
                fp.write(decoded_content)
            return dict(status='OK', data=f"File {filename} berhasil diupload")
        except IndexError:
            return dict(status='ERROR', data='Format UPLOAD: UPLOAD <nama_file> <base64_content>')
        except Exception as e:
            return dict(status='ERROR', data=f"Gagal upload file: {str(e)}")

    def delete(self, params=[]):
        try:
            if len(params) < 1:
                return dict(status='ERROR', data='Parameter tidak lengkap. Dibutuhkan nama file')
                
            filename = params[0]
            
            if not filename:
                return dict(status='ERROR', data='Nama file tidak boleh kosong')
            if os.path.exists(f"{filename}"):
                os.remove(f"{filename}")
                return dict(status='OK', data=f"File {filename} berhasil dihapus")
            else:
                return dict(status='ERROR', data=f"File {filename} tidak ditemukan")
        except IndexError:
            return dict(status='ERROR', data='Format DELETE: DELETE <nama_file>')
        except Exception as e:
            return dict(status='ERROR', data=f"Gagal menghapus file: {str(e)}")

if __name__=='__main__':
    f = FileInterface()
    print(f.list())
    print(f.get(['pokijan.jpg']))
    
    """
    # Test upload file
    print("\n=== Upload File ===")
    data = f.get(['kentang.jpg'])
    if data['status'] == 'OK':
        upload_result = f.upload(['kentang_copy.jpg', data['data_file']])
        print(upload_result)
    else:
        print(f"Gagal membaca kentang.jpg: {kentang_data}")
    """

    """
    # Test delete file
    print("\n=== Delete Files ===")
    print(f.delete(['kentang_copy.jpg']))
    """