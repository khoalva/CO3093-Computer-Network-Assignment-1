from User import User
import uuid
def app():
    id = uuid.getnode()
    username = input("username: ")
    password = input("password: ")
    user = User(id, username, password)

    x = int(input("1. Share 2. Download\n"))
    if x == 1:
        filePath = input('File Path: ')
        user.upload_file(filePath=filePath)
    else:
        fileID = input('ID: ')
        total_chunks = int(input('Chunks: '))
        user.download_file(fileID, total_chunks)

app()