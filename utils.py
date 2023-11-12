from st_files_connection import FilesConnection
import streamlit as st
from PIL import Image
import boto3
import io


def get_connection():
    try:
        conn = st.connection('s3', type=FilesConnection)
    except:
        raise Exception("connection failed")
    return conn

def s3_image_reader(bucket,key):
    session = boto3.Session(
        aws_access_key_id=st.secrets['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=st.secrets['AWS_SECRET_ACCESS_KEY'])
    
    s3_resource = session.resource('s3')
    bucket = s3_resource.Bucket(bucket)
    image = bucket.Object(key)
    img_data = image.get().get('Body').read()

    return Image.open(io.BytesIO(img_data))
