import threading
import socket
from FileHandler import FileHandler, FileChunk
import random
import time
import struct

# TRACKER_HOST = '20.2.250.184'
TRACKER_PORT = 5050
TRACKER_HOST = 'localhost'
class Peer:
    def __init__(self, peer_host, peer_port):
        self.peerHost = peer_host
        self.peerPort = peer_port
        self.is_running = False
        self.peer_server_thread = None  # Thêm thuộc tính lưu thread của server
        self.fileID = None
        self.chunks = []
        self.bitField = None
        self.totalChunks = 0


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
        server_socket.bind(('0.0.0.0', self.peerPort))
        server_socket.listen(5)
        print(f"Peer server is running at {self.peerHost}:{self.peerPort}...")

        while self.is_running:
            conn, addr = server_socket.accept()
            print(f"Connection from {addr}")

            # Nhận yêu cầu từ peer khác (ví dụ yêu cầu tải file)
            request = conn.recv(1024).decode()
            print(f"Received request: {request}")
            
            if request.startswith('BITFIELD'):
                _, fileID = request.split()

                bitfield_message = struct.pack('B' * len(self.bitField), *self.bitField)
                conn.sendall(bitfield_message)
            elif request.startswith('GET'):
                # Giả định request có dạng: "fileID chunk_num"
                _, fileID, chunk_num = request.split()
                chunk_num = int(chunk_num)
                
                # Kiểm tra xem fileID có trong danh sách chia sẻ và chunk đã được tải chưa
                if fileID == self.fileID and self.bitField[chunk_num] == 1:
                    # Nếu chunk đã tải, gửi chunk tương ứng
                    conn.sendall(self.chunks[chunk_num].to_bytes())
                    print(f"Sent chunk {chunk_num} of file {fileID} to {addr}")
                else:
                    # Nếu chunk chưa được tải hoặc file không có, báo lỗi
                    conn.sendall(b"Chunk not available or file not shared.")
            
            conn.close()

    def share_file(self, filePath):
        """Bắt đầu chia sẻ file và mở server nếu cần."""

        file = FileHandler(filePath)
        self.fileID = file.fileID
        self.chunks = file.fileChunks
        self.bitField = [1] * file.getTotalChunks()

        # Khởi động server P2P nếu chưa chạy
        self.start_peer_server()

        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            # Kết nối tới Tracker Server
            client_socket.connect((TRACKER_HOST, TRACKER_PORT))
            
            # Tạo request đăng ký chia sẻ file với Tracker Server
            request = f"POST {file.fileID} {file.getTotalChunks()} {self.peerHost} {self.peerPort}"
            print(request)
            # Gửi request
            client_socket.sendall(request.encode())
            
            # Nhận phản hồi từ server
            response = client_socket.recv(1024).decode()
            print("Response from server:", response)
        
        finally:
            # Đóng kết nối
            client_socket.close()

    def download_file(self, fileID: str, totalChunks: int):
        """Download file từ các peer và có thể mở server chia sẻ lại ngay khi tải được một phần."""
        self.fileID = fileID
        self.chunks = [FileChunk] * int(totalChunks)
        self.bitField = [0] * int(totalChunks)
        self.numDownloaded = 0
        self.totalChunks = totalChunks
        # Khởi động server để chia sẻ các phần đã tải (nếu cần)
        self.start_peer_server()

        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((TRACKER_HOST, TRACKER_PORT))
        request = f"GET {fileID}"
        client_socket.sendall(request.encode())
        response = client_socket.recv(1024).decode()        
        print('List: \n',response)

        peers = response.split('\n')
        

        neighbors = []
        for peer in peers:
            ip, port = peer.split(':')
            port = int(port)
            neighbor = self.generate_neighbor(self.fileID, ip, port)
            neighbors.append(neighbor)
        
        while self.numDownloaded < self.totalChunks:

            neededChunks = self.get_needed_chunks()
            # Tìm mảnh tệp hiếm nhất
            rarest_chunk = self.get_rarest_chunk(neighbors, needed_chunks=neededChunks)
            print('rarest_chunk: ', rarest_chunk)
            # Chọn peer tốt nhất để tải mảnh này
            best_peer = self.choose_best_peer(neighbors, rarest_chunk)
            
            if best_peer:
                # Kết nối và yêu cầu mảnh tệp
                
                conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                conn.connect((best_peer['ip'], best_peer['port']))
                
                request = f'GET {self.fileID} {rarest_chunk}'
                conn.sendall(request.encode())
                file_chunk = FileChunk(rarest_chunk, conn.recv(1024))
                
                # Kiểm tra tính toàn vẹn của mảnh tệp (giả lập kiểm tra hash)
                self.numDownloaded = self.numDownloaded + 1
                self.bitField[rarest_chunk] = 1
                self.chunks[rarest_chunk] = file_chunk
                print(f"Đã tải thành công mảnh {rarest_chunk} từ peer {best_peer['ip']}:{best_peer['port']}")

            else:
                print(f"Không tìm thấy peer có mảnh {rarest_chunk} hoặc tất cả đều bị choke.")
        
        self.combine_chunks()

    def generate_neighbor(self, fileID, ip, port):
        connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        connection.connect((ip, port))

        # Gửi yêu cầu nhận Bitfield từ peer
        request_message = f'BITFIELD {fileID}'
        connection.sendall(request_message.encode())
        
        # Nhận Bitfield từ peer
        bitfield_data = connection.recv(1024)  # Giả sử 1024 byte đủ để lưu Bitfield

        # Giải mã Bitfield và lưu lại các mảnh tệp mà peer này có
        chunks = []
        bitfield = struct.unpack('B' * len(bitfield_data), bitfield_data)
        for i, bit in enumerate(bitfield):
            if bit == 1:
                chunks.append(i)  # Peer có mảnh tệp thứ i
        return {'ip' : ip,'port' : port, 'chunks': chunks}

    def get_needed_chunks(self):
        neededChunks = []
        for i, bit in enumerate(self.bitField):
            if bit == 0:
                neededChunks.append(i)
        return neededChunks
    def get_rarest_chunk(self, peers, needed_chunks):
        # Tìm mảnh tệp hiếm nhất mà chúng ta chưa có
        chunk_count = {chunk: 0 for chunk in needed_chunks}
        for peer in peers:
            for chunk in peer['chunks']:
                if chunk in chunk_count:
                    chunk_count[chunk] += 1
        
        # Sắp xếp theo số lần xuất hiện tăng dần
        rarest_chunk = sorted(chunk_count.items(), key=lambda item: item[1])[0][0]
        return rarest_chunk

    def choose_best_peer(self, peers, chunk_index):
        # Chọn peer có mảnh tệp theo các tiêu chí: tốc độ, unchoke, độ trễ
        available_peers = [peer for peer in peers if chunk_index in peer['chunks']]
        
        if not available_peers:
            return None  # Không có peer nào có mảnh tệp này
        return available_peers[0]  

    def combine_chunks(self, output_file: str="Download.docx"):
        """
        Combine a list of FileChunk objects into a complete file.

        :param file_chunks: List of FileChunk objects.
        :param output_file: The path where the combined file will be saved.
        """
        # Sắp xếp các chunk dựa trên chunkID để đảm bảo thứ tự đúng
        self.chunks.sort(key=lambda chunk: chunk.chunkID)

        # Mở file output ở chế độ ghi nhị phân (binary mode)
        with open(output_file, 'wb') as f:
            for chunk in self.chunks:
                # Ghi dữ liệu chunk vào file
                f.write(chunk.to_bytes())

        print(f"File has been successfully reconstructed and saved at: {output_file}")

    def verify_file_integrity(self, fileID: str):
        """Giả lập kiểm tra tính toàn vẹn của file sau khi tải xong."""
        print(f"Verifying integrity of {fileID}...")


