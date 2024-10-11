import uuid
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from User import User

class FileApp:
    def __init__(self, root):
        self.root = root
        self.root.title("File Sharing App")
        self.user = None

        # Login Frame
        self.login_frame = tk.Frame(self.root)
        self.login_frame.pack(pady=20)

        tk.Label(self.login_frame, text="Username:").grid(row=0, column=0)
        self.username_entry = tk.Entry(self.login_frame)
        self.username_entry.grid(row=0, column=1)

        tk.Label(self.login_frame, text="Password:").grid(row=1, column=0)
        self.password_entry = tk.Entry(self.login_frame, show="*")
        self.password_entry.grid(row=1, column=1)

        self.login_button = tk.Button(self.login_frame, text="Login", command=self.login)
        self.login_button.grid(row=2, columnspan=2, pady=10)

        # Menu Frame (hidden until login)
        self.menu_frame = tk.Frame(self.root)

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        if username and password:
            user_id = uuid.getnode()
            self.user = User(user_id=user_id, username=username, password=password)
            messagebox.showinfo("Success", "Logged in successfully!")
            self.show_menu()
        else:
            messagebox.showerror("Error", "Please enter both username and password")

    def show_menu(self):
        self.login_frame.pack_forget()
        self.menu_frame.pack(pady=20)

        tk.Button(self.menu_frame, text="Upload File", command=self.upload_file).pack(pady=5)
        tk.Button(self.menu_frame, text="Download File", command=self.download_file).pack(pady=5)
        tk.Button(self.menu_frame, text="Exit", command=self.root.quit).pack(pady=5)

    def upload_file(self):
        file_path = filedialog.askopenfilename(title="Select a file")
        if file_path:
            self.user.upload_file(filePath=file_path)
            messagebox.showinfo("Success", "File uploaded successfully!")
        else:
            messagebox.showerror("Error", "No file selected")

    def download_file(self):
        file_id = simpledialog.askstring("File Download", "Enter File ID")
        total_chunks = simpledialog.askstring("File Download", "Enter File Total chunks")
        if file_id:
            self.user.download_file(fileID=file_id, totalChunks=int(total_chunks))
            messagebox.showinfo("Success", "File downloaded successfully!")
        else:
            messagebox.showerror("Error", "No File ID entered")


if __name__ == "__main__":
    root = tk.Tk()
    app = FileApp(root)
    root.mainloop()
