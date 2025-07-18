import socket
import threading
from typing import Dict, List

SERVER_MASK = '0.0.0.0'
SERVER_PORT = 5050

class TrackerServer:
    def __init__(self):
        self.peers: Dict[str, List[Dict[str, str, int]]] = {}  # Lưu thông tin về các peer theo fileID (name, ip, port)
        self.lock = threading.Lock()  # Để đảm bảo thread-safe khi có nhiều kết nối đồng thời
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((SERVER_MASK, SERVER_PORT))
    def start(self):
        """Khởi động server và bắt đầu lắng nghe các kết nối."""

        self.server_socket.listen(5)
        print(f"Tracker server is running...")
        while True:
            client_socket, addr = self.server_socket.accept()
            print(f"Connection from {addr}")
            threading.Thread(target=self.handle_client, args=(client_socket,)).start()

    def close(self):
        self.server_socket.close()

    def handle_client(self, client_socket: socket.socket):
        """Xử lý các yêu cầu từ client."""
        try:
            request = client_socket.recv(1024).decode('utf-8')
            if request.startswith("POST"):
                _, file_name, file_id, totalChunks, ip, port = request.split()
                self.register_peer(file_name, file_id, ip, int(port))
                response = f"Post peer {ip}:{port} for fileID {file_id} TotalChunks {totalChunks}"
                client_socket.send(response.encode('utf-8'))
            elif request.startswith("GET"):
                _, file_id = request.split()
                peers = self.get_peers(file_id)
                response = "\n".join(peers) if peers else "No peers available."
                client_socket.send(response.encode('utf-8'))
            elif request.startswith("DELETE"):
                _, file_id, ip, port = request.split()
                self.remove_peer(file_id, ip, int(port))
                response = f"Deleted peer {ip}:{port} for fileID {file_id}"
                client_socket.send(response.encode('utf-8'))
            else:
                client_socket.send(b"Invalid request.")
        finally:
            client_socket.close()

    def register_peer(self, file_name: str, file_id: str, ip: str, port: int):
        """Đăng ký peer vào danh sách chia sẻ file."""
        with self.lock:
            if file_id not in self.peers:
                self.peers[file_id] = []
            
            self.peers[file_id].append({'name': file_name, 'ip': ip, 'port': port})
            print(f"Peer registered: {ip}:{port} for fileID {file_id} with fileName {file_name}")

    def get_peers(self, file_id: str) -> List[str]:
        """Trả về danh sách các peer chia sẻ fileID."""
        with self.lock:
            
            return [f"{peer['name']}:{peer['ip']}:{peer['port']}" for peer in self.peers.get(file_id, [])]

    def remove_peer(self, file_id: str, ip: str, port: int):
        """Xóa peer khỏi danh sách chia sẻ file."""
        with self.lock:
            if file_id in self.peers:
                self.peers[file_id] = [
                    peer for peer in self.peers[file_id]
                    if not (peer['ip'] == ip and peer['port'] == port)
                ]
                if not self.peers[file_id]:  # Xóa key nếu không còn peer
                    del self.peers[file_id]
            print(f"Peer removed: {ip}:{port} for fileID {file_id}")

if __name__ == "__main__":
    tracker = TrackerServer()
    tracker.start()