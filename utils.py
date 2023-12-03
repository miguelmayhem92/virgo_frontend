from st_files_connection import FilesConnection
import streamlit as st
from PIL import Image
import boto3
import io
from streamlit_extras.app_logo import add_logo
import plotly
import json

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
from streamlit_extras.app_logo import add_logo


def logo(debug_mode):
    if debug_mode:
        add_logo(".\images\log_white.png", height=150)
    else:
        add_logo("log_white.png", height=150)


def print_object(name, type, symbol_name, debug_mode = True, local_storage =True, conn = False):

    if type == 'plot':
        try:
            if debug_mode:
                fig = plotly.io.read_json(f'{local_storage}/{symbol_name}/{name}')
            else:
                jsonfile = conn.read(f"virgo-data/market_plots/{symbol_name}/{name}", input_format="json", ttl=30)
                json_dump = json.dumps(jsonfile)
                fig = plotly.io.from_json(json_dump)

            st.plotly_chart(fig, theme="streamlit", use_container_width=True)
        except:
            st.write("no plot available :(")
    elif type == 'message':
        try:
            if debug_mode:
                market_message = json.load(open(f'{local_storage}/{symbol_name}/{name}'))
            else:
                market_message = conn.read(f"virgo-data/market_plots/{symbol_name}/{name}", input_format="json", ttl=30)

            message1 = market_message['current_state']
            message2 = market_message['current_step_state']
            message3 = market_message['report_date']
            st.write(f"status:")
            st.write(f"{message1}")
            st.write(f"{message2}")
            st.write(f"{message3}")
        except:
            st.write("no text was recorded :(")