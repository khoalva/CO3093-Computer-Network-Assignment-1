import os
import hashlib
import struct

class FileChunk:
    def __init__(self, chunkID: int, data: bytes):
        """
        Initialize a FileChunk with a chunkID and the chunk data.
        :param chunkID: The unique ID of the chunk (often its index in the file).
        :param data: The actual binary data of the chunk.
        """
        self.chunkID = chunkID
        self.data = data
        self.chunkHash = self.calculate_hash()  # Store the hash for integrity checking

    def calculate_hash(self) -> str:
        """
        Calculate the hash of the chunk data for integrity checking.
        :return: A string representing the hash of the chunk.
        """
        return hashlib.sha256(self.data).hexdigest()

    def verify_integrity(self, expected_hash: str) -> bool:
        """
        Verify the integrity of the chunk by comparing the calculated hash with the expected hash.
        :param expected_hash: The expected hash value of the chunk.
        :return: True if the chunk's hash matches the expected hash, False otherwise.
        """
        return self.chunkHash == expected_hash

    def get_size(self) -> int:
        """
        Get the size of the chunk in bytes.
        :return: The size of the chunk.
        """
        return len(self.data)
    def to_bytes(self):
        """
        Convert the FileChunk instance to a bytes object.
        The format will be: [chunkID (4 bytes)] + [data]
        :return: A bytes object that contains the chunkID followed by the chunk data.
        """
        # Use struct to pack the chunkID (as 4 bytes) and append the data.
        return struct.pack('!I', self.chunkID) + self.data
    
    @staticmethod
    def from_bytes(byte_data: bytes):
        """
        Decode a bytes object back into a FileChunk instance.
        Expects the format: [chunkID (4 bytes)] + [data]
        :param byte_data: A bytes object that contains the chunkID followed by the chunk data.
        :return: A FileChunk instance.
        """
        # Extract the first 4 bytes as the chunkID, and the rest as the data.
        chunkID = struct.unpack('!I', byte_data[:4])[0]
        data = byte_data[4:]
        return FileChunk(chunkID, data)


class FileHandler:
    def __init__(self, file_path: str,  chunk_size: int = 8192):
        """
        Initialize the File class with a file path and chunk size.
        :param file_path: Path to the file on the local system.
        :param chunk_size: Size of each chunk in bytes (default is 8192).
        """
        fileName =  os.path.basename(file_path)
        self.fileName = fileName
        self.filePath = file_path
        self.fileSize = self.get_file_size()
        self.fileHash = self.calculate_hash()
        self.chunkSize = chunk_size
        self.fileChunks = self.create_file_chunks()
        self.totalChunks = self.getTotalChunks()
        self.fileID = self.generate_file_id(self.fileSize, self.fileHash, self.totalChunks, self.chunkSize)

    def generate_file_id(self, size, hashCode, numChunks, chunkSize) -> str:
        """
        Tạo ra fileID bằng cách kết hợp metadata như fileSize và fileHash.
        :return: Chuỗi fileID duy nhất.
        """
        # Tận dụng metadata để tạo fileID
        metadata_str = f"{size}_{hashCode}_{numChunks}_{chunkSize}"
        return hashlib.sha256(metadata_str.encode()).hexdigest()
    def get_file_size(self) -> int:
        """Returns the file size in bytes."""
        try:
            return os.path.getsize(self.filePath)
        except OSError:
            raise FileNotFoundError(f"File not found: {self.filePath}")

    def calculate_hash(self) -> str:
        """Calculates the SHA-256 hash of the entire file."""
        sha256 = hashlib.sha256()
        try:
            with open(self.filePath, 'rb') as f:
                while chunk := f.read(8192):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except OSError:
            raise FileNotFoundError(f"Unable to open file: {self.filePath}")

    def create_file_chunks(self) -> list:
        """
        Divides the file into smaller chunks of data.
        :return: A list of FileChunk objects representing the file chunks.
        """
        chunks = []
        try:
            with open(self.filePath, 'rb') as f:
                chunk_id = 0
                while data := f.read(self.chunkSize):
                    chunk = FileChunk(chunkID=chunk_id, data=data)
                    chunks.append(chunk)
                    chunk_id += 1
        except OSError:
            raise FileNotFoundError(f"Unable to open file: {self.filePath}")
        chunks.sort(key=lambda chunk: chunk.chunkID)
        return chunks

    def get_metadata(self) -> dict:
        """Returns metadata of the file including name, ID, size, and hash."""
        return {
            'fileName': self.fileName,
            'fileID': self.fileID,
            'fileSize': self.fileSize,
            'fileHash': self.fileHash
        }

    def get_chunk(self, chunk_id: int) -> FileChunk:
        """
        Retrieves a specific file chunk by its ID.
        :param chunk_id: The ID of the chunk to retrieve.
        :return: The FileChunk object if it exists, otherwise raises IndexError.
        """
        if chunk_id < 0 or chunk_id >= len(self.fileChunks):
            raise IndexError(f"Chunk ID {chunk_id} is out of range.")
        return self.fileChunks[chunk_id]

    def get_all_chunks(self) -> list:
        """Returns a list of all file chunks."""
        return self.fileChunks

    def getTotalChunks(self):
        return len(self.fileChunks)

    @staticmethod
    def combine_chunks(chunks, output_file: str="download.txt"):
        """
        Combine a list of FileChunk objects into a complete file.

        :param file_chunks: List of FileChunk objects.
        :param output_file: The path where the combined file will be saved.
        """
        # Sắp xếp các chunk dựa trên chunkID để đảm bảo thứ tự đúng
        chunks.sort(key=lambda chunk: chunk.chunkID)

        # Mở file output ở chế độ ghi nhị phân (binary mode)
        with open(output_file, 'wb') as f:
            for chunk in chunks:
                # Ghi dữ liệu chunk vào file
                f.write(chunk.data)
        
        print(f"File has been successfully reconstructed and saved at: {output_file}")


# file = FileHandler('test.txt')
# file.combine_chunks(file.fileChunks, 'test2.txt')

