import socket
from Peer import Peer

class User:
    def __init__(self, user_id, username, password):
        self.userID = user_id          # Unique ID for the user
        self.username = username       # Username for authentication
        self.password = password       # Password for authentication
        self.peerList = []  # Initialize peer list

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

        peer_host, peer_port = self.get_ip_port() 
        peer = Peer(peer_host, peer_port)
        self.peerList.append(peer)
        peer.share_file(filePath)

    # Request to download a file
    def download_file(self, fileID: str, totalChunks: int):
        print(f"User {self.username} requests to download file: {fileID}")

        peer_host, peer_port = self.get_ip_port() 
        print(peer_host, peer_port)
        peer = Peer(peer_host, peer_port)
        self.peerList.append(peer)
        peer.download_file(fileID, totalChunks)


    def stop(self, peerID):
        self.peerList[peerID].stop_peer_server()

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


