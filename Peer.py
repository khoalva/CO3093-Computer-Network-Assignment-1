import threading
import os
import socket
from FileHandler import FileHandler
from TrackerServer import TrackerServer
TRACKER_HOST = 'localhost'
TRACKER_PORT = 5000

class Peer:
    def __init__(self, peer_host, peer_port):
        self.peerHost = peer_host
        self.peerPort = peer_port
        self.is_running = False
        self.sharedFiles = {}  # Sửa thành dictionary lưu fileID và các chunks đã tải được
        self.downloadedFiles = []
        self.peer_server_thread = None  # Thêm thuộc tính lưu thread của server
    
    def start_peer_server(self):
        """Khởi chạy server để lắng nghe các yêu cầu từ peer khác."""
        if not self.is_running:
            self.is_running = True
            self.peer_server_thread = threading.Thread(target=self.peer_server)
            self.peer_server_thread.start()

    def stop_peer_server(self):
        """Dừng server P2P khi không cần nữa."""
        if self.is_running:
            self.is_running = False
            if self.peer_server_thread:
                self.peer_server_thread.join()
            print(f"Peer server at {self.peerHost}:{self.peerPort} has stopped.")
    
    def peer_server(self):
        """Peer server để lắng nghe các yêu cầu download từ các peer khác."""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.peerHost, self.peerPort))
        server_socket.listen(5)
        print(f"Peer server is running at {self.peerHost}:{self.peerPort}...")

        while self.is_running:
            conn, addr = server_socket.accept()
            print(f"Connection from {addr}")

            # Nhận yêu cầu từ peer khác (ví dụ yêu cầu tải file)
            request = conn.recv(1024).decode()
            print(f"Received request: {request}")
            
            # Giả định request có dạng: "fileID chunk_num"
            fileID, chunk_num = request.split()
            chunk_num = int(chunk_num)
            
            # Kiểm tra xem fileID có trong danh sách chia sẻ và chunk đã được tải chưa
            if fileID in self.sharedFiles and chunk_num in self.sharedFiles[fileID]:
                # Nếu chunk đã tải, gửi chunk tương ứng
                chunk_data = self.sharedFiles[fileID][chunk_num]
                conn.sendall(chunk_data)
                print(f"Sent chunk {chunk_num} of file {fileID} to {addr}")
            else:
                # Nếu chunk chưa được tải hoặc file không có, báo lỗi
                conn.sendall(b"Chunk not available or file not shared.")
            
            conn.close()

    def share_file(self, file: FileHandler):
        """Bắt đầu chia sẻ file và mở server nếu cần."""
        # Tính toán hash của file và chia nhỏ file thành các chunks
        self.sharedFiles[file.fileID] = self.split_file_into_chunks(file.filePath)
        
        # Khởi động server P2P nếu chưa chạy
        self.start_peer_server()

        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            # Kết nối tới Tracker Server
            client_socket.connect((TRACKER_HOST, TRACKER_PORT))
            
            # Tạo request đăng ký chia sẻ file với Tracker Server
            request = f"POST {file.fileID} {self.peerHost} {self.peerPort}"
            print(request)
            # Gửi request
            client_socket.sendall(request.encode())
            
            # Nhận phản hồi từ server
            response = client_socket.recv(1024).decode()
            print("Response from server:", response)
        
        finally:
            # Đóng kết nối
            client_socket.close()

    def stop_sharing(self, fileID: str):
        """Ngừng chia sẻ file và tắt server nếu không có file nào được chia sẻ."""
        if fileID in self.sharedFiles:
            del self.sharedFiles[fileID]
            print(f"Stopped sharing file {fileID}.")
        
        # Nếu không còn file nào để chia sẻ, dừng server
        if not self.sharedFiles:
            self.stop_peer_server()

    def download_file(self, fileID: str):
        """Download file từ các peer và có thể mở server chia sẻ lại ngay khi tải được một phần."""
        # Khởi động server để chia sẻ các phần đã tải (nếu cần)
        self.start_peer_server()

        metadata = {}  # Giả lập metadata từ Tracker Server
        peers = metadata.get('peers', [])
        
        # Tạo một dictionary trống để lưu các chunks của file
        if fileID not in self.sharedFiles:
            self.sharedFiles[fileID] = {}

        # Giả lập quá trình tải file song song từ nhiều peer
        threads = []
        for peer in peers:
            thread = threading.Thread(target=self.download_from_peer, args=(fileID, peer))
            threads.append(thread)
            thread.start()

        # Chờ các thread tải xong
        for thread in threads:
            thread.join()

        # Sau khi tải xong toàn bộ file, dừng server nếu không có hoạt động chia sẻ
        self.stop_peer_server()

    def download_from_peer(self, fileID: str, peer: str):
        """Giả lập việc tải file từ một peer."""
        print(f"Downloading file {fileID} from peer {peer}...")

        # Giả lập tải chunk từ peer
        for chunk_num in range(3):  # Giả định có 3 chunks
            # Giả lập việc nhận chunk từ peer
            chunk_data = f"chunk_data_{chunk_num}".encode()
            self.sharedFiles[fileID][chunk_num] = chunk_data
            print(f"Downloaded chunk {chunk_num} of file {fileID} from peer {peer}.")

    def split_file_into_chunks(self, file_path: str):
        """Chia file thành các chunks để chia sẻ (giả lập)."""
        # Giả lập tách file thành các chunk, có thể lưu vào dict.
        return {
            0: b"chunk_data_1", 
            1: b"chunk_data_2", 
            2: b"chunk_data_3"
        }

    def verify_file_integrity(self, fileID: str):
        """Giả lập kiểm tra tính toàn vẹn của file sau khi tải xong."""
        print(f"Verifying integrity of {fileID}...")
