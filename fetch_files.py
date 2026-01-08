import paramiko
import os

HOST = "ANDIJON_SERVER_IP"
PORT = 22  
USERNAME = "USER_NAME"
PASSWORD = "PASSWORD"  
SOURCE_DIR = "/app/andijon_files" 
DEST_DIR = "/app/toshkent_files"  

def download_files():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, port=PORT, username=USERNAME, password=PASSWORD)
    
    sftp = ssh.open_sftp()
    
    
    if not os.path.exists(DEST_DIR):
        os.makedirs(DEST_DIR)
    
    
    for filename in sftp.listdir(SOURCE_DIR):
        source_file = os.path.join(SOURCE_DIR, filename)
        dest_file = os.path.join(DEST_DIR, filename)
        sftp.get(source_file, dest_file)
        print(f"{filename} yuklandi.")
    
    sftp.close()
    ssh.close()
    print("Barcha fayllar muvaffaqiyatli yuklandi!")

if __name__ == "__main__":
    download_files()
