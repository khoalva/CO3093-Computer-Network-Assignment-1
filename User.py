import socket
from FileHandler import FileHandler
from Peer import Peer
class User:
    def __init__(self, user_id, username, password):
        self.userID = user_id          # Unique ID for the user
        self.username = username       # Username for authentication
        self.password = password       # Password for authentication
        peer_host, peer_port = self.get_ip_port()  # Get IP and port automatically
        self.peer = Peer(peer_host=peer_host, peer_port=peer_port)  # Initialize peer

    def register(self):
        pass

    # Authenticate user based on provided username and password
    def login(self, username, password):
        if self.username == username and self.password == password:
            print(f"User {self.username} logged in successfully.")
            return True
        else:
            print(f"Login failed for {self.username}.")
            return False

    # Log out the user
    def logout(self):
        print(f"User {self.username} logged out.")
    
    # Request to upload a file (share)
    def upload_file(self, filePath):
        print(f"User {self.username} requests to upload file: {filePath}")
        try:
            file = FileHandler(file_path=filePath)
        except:
            raise "Error"
        self.peer.share_file(file)

    # Request to download a file
    def download_file(self, fileID):
        print(f"User {self.username} requests to download file: {fileID}")
        try:
            self.peer.download_file(fileID)
        except:
            print("Download error!")

    def stop_sharing(self, fileID):
        self.peer.stop_sharing(fileID=fileID)

    def get_ip_port(self):
        """Lấy địa chỉ IP và tìm một cổng trống cho Peer."""
        # Lấy địa chỉ IP của máy người dùng
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)

        # Tìm một port trống để dùng
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))  # Bind tới bất kỳ cổng trống nào (0 là chỉ định hệ thống tự tìm port)
            port = s.getsockname()[1]  # Lấy port đã bind
        return ip_address, port


