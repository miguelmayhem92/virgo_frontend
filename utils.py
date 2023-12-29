from st_files_connection import FilesConnection
import streamlit as st
from PIL import Image
import boto3
import io
from streamlit_extras.app_logo import add_logo
import plotly
import json
import pandas as pd
import requests

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
        add_logo("https://raw.githubusercontent.com/miguelmayhem92/virgo_frontend/main/images/log_white.png", height=150)

def execute_asset_lambda(payload):
    url = st.secrets['deep_dive_asset_api_url']
    headers = {'X-API-Key':st.secrets['deep_dive_asset_api_key']}
    response = requests.post(url, json  = payload, headers=headers)
    result = json.loads(response.text)
    if result["body"] == "success lambda execution":
        print(result["body"])
    else:
        raise Exception('Error with lambda')
    


def print_object(name, type, symbol_name, debug_mode = True, local_storage =True, conn = False, streamlit_conn = True, bucket = False):

    if type == 'plot':
        try:
            if debug_mode:
                fig = plotly.io.read_json(f'{local_storage}/{symbol_name}/{name}')
            else:
                if streamlit_conn:
                    jsonfile = conn.read(f"virgo-data/market_plots/{symbol_name}/{name}", input_format="json", ttl=30)
                    json_dump = json.dumps(jsonfile)
                    fig = plotly.io.from_json(json_dump)
                else:
                    session = boto3.Session(
                        aws_access_key_id=st.secrets['AWS_ACCESS_KEY_ID'],
                        aws_secret_access_key=st.secrets['AWS_SECRET_ACCESS_KEY'])
                    s3_resource = session.resource('s3')
                    bucket = s3_resource.Bucket(bucket)
                    image = bucket.Object(f"market_plots/{symbol_name}/{name}")
                    jsonfile = image.get().get('Body').read().decode()
                    json_dump = jsonfile
                    fig = plotly.io.from_json(json_dump)

            st.plotly_chart(fig, theme="streamlit", use_container_width=True)
        except:
            st.write("no plot available :(")
    elif type == 'message':
        try:
            if debug_mode:
                market_message = json.load(open(f'{local_storage}/{symbol_name}/{name}'))
            else:
                if streamlit_conn:
                    market_message = conn.read(f"virgo-data/market_plots/{symbol_name}/{name}", input_format="json", ttl=30)
                else:
                    session = boto3.Session(
                        aws_access_key_id=st.secrets['AWS_ACCESS_KEY_ID'],
                        aws_secret_access_key=st.secrets['AWS_SECRET_ACCESS_KEY'])
                    s3_resource = session.resource('s3')
                    bucket = s3_resource.Bucket(bucket)
                    image = bucket.Object(f"market_plots/{symbol_name}/{name}")
                    jsonfile = image.get().get('Body').read().decode()
                    market_message = json.loads(jsonfile)

            st.write(f"status:")
            for key in market_message.keys():
                message = market_message.get(key)
                st.write(f"{message}")

        except:
            st.write("no text was recorded :(")

    elif type == 'csv':
        try:
            if debug_mode:
                
                df = pd.read_csv(f'{local_storage}/{symbol_name}/{name}')
            else:
                if streamlit_conn:
                    df = conn.read(f"virgo-data/market_plots/{symbol_name}/{name}", input_format="csv", ttl=30)
                else:
                    session = boto3.Session(
                        aws_access_key_id=st.secrets['AWS_ACCESS_KEY_ID'],
                        aws_secret_access_key=st.secrets['AWS_SECRET_ACCESS_KEY'])
                    s3_resource = session.resource('s3')
                    bucket = s3_resource.Bucket(bucket)
                    image = bucket.Object(f"market_plots/{symbol_name}/{name}")
                    jsonfile = image.get().get('Body').read()
                    df = pd.read_csv(io.BytesIO(jsonfile))
            st.dataframe(df)
        except:
            st.write("no csv was recorded :(")
