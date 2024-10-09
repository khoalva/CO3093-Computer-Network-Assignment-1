import streamlit as st
import uuid
from User import User

def app():
    st.title("File Sharing Application")

    # Generate a unique user ID
    userID = uuid.getnode()

    # User login
    username = st.text_input("Username:")
    password = st.text_input("Password:", type="password")

    if st.button("Login"):
        user = User(user_id=userID, username=username, password=password)
        st.session_state["user"] = user
        st.success("Logged in successfully!")

    if "user" in st.session_state:
        user = st.session_state["user"]

        st.subheader("Select an option")
        option = st.selectbox("Choose an option:", ["Share", "Download", "Exit"])

        if option == "Share":
            filePath = st.text_input("File Path:")
            if st.button("Upload File"):
                if filePath:
                    user.upload_file(filePath)
                    st.success("File uploaded successfully!")
                else:
                    st.error("Please provide a file path.")
        
        elif option == "Download":
            fileID = st.text_input("File ID:")
            if st.button("Download File"):
                if fileID:
                    user.download_file(fileID)
                    st.success("File downloaded successfully!")
                else:
                    st.error("Please provide a file ID.")
        
        elif option == "Exit":
            st.info("Thank you for using the app!")
            st.stop()

if __name__ == "__main__":
    app()
