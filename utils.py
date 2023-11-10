from st_files_connection import FilesConnection
import streamlit as st

def get_connection():
    try:
        conn = st.connection('s3', type=FilesConnection)
    except:
        raise Exception("connection failed")
    return conn