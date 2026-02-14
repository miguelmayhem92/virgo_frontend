from st_files_connection import FilesConnection
import streamlit as st
from PIL import Image
import boto3
import io
import time
import uuid
from streamlit_extras.app_logo import add_logo
import plotly
import json
import pandas as pd
import requests
import numpy as np
from virgo_modules.src.ticketer_source import stock_eda_panel
from sklearn.metrics import precision_score, recall_score
import yfinance as yf

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

def logo(debug_mode):
    if debug_mode:
         st.sidebar.image(".\images\Virgo_blanco_resize.png",use_column_width=True) 
    else:
         st.sidebar.image("https://raw.githubusercontent.com/miguelmayhem92/virgo_frontend/main/images/Virgo_blanco_resize.png",use_column_width=True)
    st.sidebar.title("Statistical arbitrage")
    
def execute_asset_lambda(payload):
    try:
        url = st.secrets['deep_dive_asset_api_url']
        headers = {'X-API-Key':st.secrets['api_key']}
        response = requests.post(url, json  = payload, headers=headers)
        result = json.loads(response.text)
        if result["body"] == "success lambda execution":
            print(result["body"])
    except:
        st.error('error with lambda execution', icon="🚨")

def execute_edgemodel_lambda(payload):
    try:
        url = st.secrets['edge_models_api_url']
        headers = {'X-API-Key':st.secrets['api_key']}
        response = requests.post(url, json  = payload, headers=headers)
        result = json.loads(response.text)
        if result["body"] == "success lambda execution":
            print(result["body"])
    except:
        st.error('error with lambda execution', icon="🚨")

def execute_state_machine_allocator(payload):
    load_str = json.dumps(payload)
    payload = {
        "input": load_str,
        "name": str(uuid.uuid1()),
        "stateMachineArn": st.secrets['allocator_state_machine_arn']
    }
    url = st.secrets['call_state_machine_allocator']
    headers = {'X-API-Key': st.secrets['api_key']}
    response = requests.post(url, json  = payload, headers=headers)
    result = json.loads(response.text)
    time.sleep(10)

def read_state_machine_allocator():
    session = boto3.Session(aws_access_key_id=st.secrets['AWS_ACCESS_KEY_ID'],aws_secret_access_key=st.secrets['AWS_SECRET_ACCESS_KEY'])
    s3_resource = session.resource('s3')
    bucket = s3_resource.Bucket('virgo-data')
    

def reading_last_execution(file_name: str, folder_path: str, date_key:str):
    """
    file_name: e.g message.json
    folder_path: e.g path/folder/
    date_key: e.g. key of the date
    """
    session = boto3.Session(aws_access_key_id=st.secrets['AWS_ACCESS_KEY_ID'],aws_secret_access_key=st.secrets['AWS_SECRET_ACCESS_KEY'])
    s3_resource = session.resource('s3')
    bucket = s3_resource.Bucket('virgo-data')
    image = bucket.Object(f"{folder_path}{file_name}")
    jsonfile = image.get().get('Body').read().decode()
    message = json.loads(jsonfile)
    aws_report_date = message[date_key]
    return aws_report_date

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

def aws_print_object(file_name: str, type: str, conn = False, streamlit_conn:bool = True, bucket:str = False, folder_path:str = False):
    """
    file_name: eg. message.json
    type: values: plot, message or csv
    symbol_name: eg DIS
    conn: streamlit connectaion object
    streamlit_conn: use streamlit connection object or aws
    bucket: bucket name
    folder_path: eg. path/to/folder/
    """

    if type == 'plot':
        try:
            if streamlit_conn:
                jsonfile = conn.read(f"{bucket}/{folder_path}{file_name}", input_format="json", ttl=30)
                json_dump = json.dumps(jsonfile)
                fig = plotly.io.from_json(json_dump)
            else:
                session = boto3.Session(
                    aws_access_key_id=st.secrets['AWS_ACCESS_KEY_ID'],
                    aws_secret_access_key=st.secrets['AWS_SECRET_ACCESS_KEY'])
                s3_resource = session.resource('s3')
                bucket = s3_resource.Bucket(bucket)
                image = bucket.Object(f"{folder_path}{file_name}")
                jsonfile = image.get().get('Body').read().decode()
                json_dump = jsonfile
                fig = plotly.io.from_json(json_dump)

            st.plotly_chart(fig, theme="streamlit", use_container_width=True)
        except:
            st.write("no plot available :(")
    elif type == 'message':
        try:
            if streamlit_conn:
                market_message = conn.read(f"{bucket}/{folder_path}{file_name}", input_format="json", ttl=30)
            else:
                session = boto3.Session(
                    aws_access_key_id=st.secrets['AWS_ACCESS_KEY_ID'],
                    aws_secret_access_key=st.secrets['AWS_SECRET_ACCESS_KEY'])
                s3_resource = session.resource('s3')
                bucket = s3_resource.Bucket(bucket)
                image = bucket.Object(f"{folder_path}{file_name}")
                jsonfile = image.get().get('Body').read().decode()
                market_message = json.loads(jsonfile)

            long_message = list()
            for key in market_message.keys():
                message = " * " + str(market_message.get(key))
                long_message.append(message)
            long_message = " \n ".join(long_message)

            st.markdown("###### yield results:")
            st.markdown(long_message)

        except:
            st.write("no text was recorded :(")

    elif type == 'csv':
        try:
            if streamlit_conn:
                df = conn.read(f"{bucket}/{folder_path}{file_name}", input_format="csv", ttl=30)
            else:
                session = boto3.Session(
                    aws_access_key_id=st.secrets['AWS_ACCESS_KEY_ID'],
                    aws_secret_access_key=st.secrets['AWS_SECRET_ACCESS_KEY'])
                s3_resource = session.resource('s3')
                bucket = s3_resource.Bucket(bucket)
                image = bucket.Object(f"{folder_path}{file_name}")
                jsonfile = image.get().get('Body').read()
                df = pd.read_csv(io.BytesIO(jsonfile))
            st.dataframe(df)
        except:
            st.write("no csv was recorded :(")

def call_edge_json(file_name: str, conn = False,dict_keys=list(), streamlit_conn:bool = True, bucket:str = False, folder_path:str = False, format_values_to_perc = True):

    if streamlit_conn:
        edges_results = conn.read(f"{bucket}/{folder_path}{file_name}", input_format="json", ttl=30)
    else:
        session = boto3.Session(
            aws_access_key_id=st.secrets['AWS_ACCESS_KEY_ID'],
            aws_secret_access_key=st.secrets['AWS_SECRET_ACCESS_KEY'])
        s3_resource = session.resource('s3')
        bucket = s3_resource.Bucket(bucket)
        image = bucket.Object(f"{folder_path}{file_name}")
        jsonfile = image.get().get('Body').read().decode()
        edges_results = json.loads(jsonfile)

    if format_values_to_perc:
        for k in dict_keys:
            edges_results[k] = str(round(edges_results[k]*100,2))+'%'

    result_to_print = {k:v for k,v in edges_results.items() if k in dict_keys}
    st.markdown("###### current edges:")
    st.write(result_to_print)

def dowload_any_object(file_name, folder, file_type, bucket):
    """
    file_name 
    folder_path: eg. path/to/folder/
    file_type: csv, txt
    bucket: bucket name
    """

    session = boto3.Session(
        aws_access_key_id=st.secrets['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=st.secrets['AWS_SECRET_ACCESS_KEY'])
    s3_resource = session.resource('s3')
    bucket = s3_resource.Bucket(bucket)
    image = bucket.Object(f"{folder}{file_name}")
    jsonfile = image.get().get('Body').read()

    if file_type == 'csv':
        df = pd.read_csv(io.BytesIO(jsonfile), sep = ';')

    elif file_type == 'txt':  
        elements = jsonfile.decode("utf-8").split('\n')
        elements = [e.split(' ') for e in elements]
        arrays = list()
        for e in elements:
            string = ' '.join(e)
            array = list(np.fromstring(string, sep=' '))
            arrays.append(array)
        arrays = [e for e in arrays if len(e) > 0 ]
        df = np.array(arrays)

    elif file_type == 'json':
        df = json.loads(jsonfile)

    return df

class data_inherit_stock_eda_panel(stock_eda_panel):
    def __init__(self, data):
        self.df = data

type_map = {0:'no signal', -1: 'low signal', 1:'high signal'}

def extend_message(json_message, data_frame, signal):
    """
    extended message from signal analyser object using stock_eda_panel extended class

    arguments:
        json_message (json): json message
        data_frame (pd.DataFrame): data with features
        signal (str): feature name

    returns:
        json_message (json): resulting json message
    """
    extend_sep = data_inherit_stock_eda_panel(data_frame)
    extend_sep.produce_order_features(signal)

    current_position = extend_sep.df.iloc[-1][f'order_signal_{signal}']
    current_type = extend_sep.df.iloc[-1][f'discrete_signal_{signal}']
    type_ = type_map.get(current_type,'blurry signal')

    comp_message = f'{type_} position {current_position}'
    json_message['current signal'] = comp_message

    return json_message

def signal_position_message(data_frame, signal):

    """
    create message of the signal position of the current data

    arguments:
        data_frame (pd.DataFrame): data with features
        signal (str): feature name

    returns:
        json_message (json): resulting json message
    """
    extend_sep = data_inherit_stock_eda_panel(data_frame)
    extend_sep.produce_order_features(signal)
    current_position = extend_sep.df.iloc[-1][f'order_signal_{signal}']
    current_type = extend_sep.df.iloc[-1][f'discrete_signal_{signal}']
    type_ = type_map.get(current_type,'blurry signal')
    comp_message = f'{type_} position {current_position}'
    return {'current signal': comp_message}

def get_categorical_targets(df, horizon, flor_loss, top_gain):
    """
    produce binary target return taking future prices. it produce two targets, one for high returns and another for low returns
    this function is taken from the ticket_object

    Arguments:
        horizon (int): number of lags and steps for future returns
        flor_loss (float): min loss return
        top_gain (float): max gain return

    Returns:
        data frame with new colums
    """

    columns = list()

    ## loops
    for i in range(1,horizon+1):
        df[f'target_{i}'] = df.High.shift(-i)
        df[f'target_{i}'] = (df[f'target_{i}']/df.Open-1)*100

        df[f'target_{i}'] = np.where(df[f'target_{i}'] >= top_gain,1,0)
        columns.append(f'target_{i}')
    df[f'target_up'] = df[columns].sum(axis=1)
    df[f'target_up'] = np.where(df[f'target_up'] >=1,1,0 )
    df = df.drop(columns = columns)

    for i in range(1,horizon+1):
        df[f'target_{i}'] = df.Low.shift(-i)
        df[f'target_{i}'] = (df[f'target_{i}']/df.Open-1)*100

        df[f'target_{i}'] = np.where(df[f'target_{i}'] <= flor_loss,1,0)
        columns.append(f'target_{i}')
    df[f'target_down'] = df[columns].sum(axis=1)
    df[f'target_down'] = np.where(df[f'target_down'] >= 1,1,0 )
    df = df.drop(columns = columns)
    return df

def perf_metrics_message(data, test_data_size, edge_name):
    """
    produce summary metrics given a data sample

    Arguments:
        data (pd.DataFrame): data
        test_data_size (int): test data size
        edge_name (str): edge name

    Returns:
        metrics of edge metrics, precision and recall
    """
    df_perf = data.iloc[-test_data_size:,:][['target_up','target_down',f'signal_up_{edge_name}', f'signal_low_{edge_name}']]
    go_up_precision, go_up_recall = round(precision_score(df_perf['target_up'], df_perf[f'signal_low_{edge_name}'])*100,2), round(recall_score(df_perf['target_up'], df_perf[f'signal_low_{edge_name}'])*100,2)
    go_down_precision, go_down_recall = round(precision_score(df_perf['target_down'], df_perf[f'signal_up_{edge_name}'])*100,2), round(recall_score(df_perf['target_down'], df_perf[f'signal_up_{edge_name}'])*100,2)
    
    results = {
        'go up metrics':{
            'precision':go_up_precision, 'recall':go_up_recall
        },
        'go down metrics':{
            'precision':go_down_precision, 'recall':go_down_recall
        }
    }
    return results

def find_info(symbol):
    asset = yf.Ticker(symbol)
    sn, c, s = asset.info.get("shortName"), asset.info.get("country"), asset.info.get("sector")
    return {
        "symbol": symbol, "short_name": sn, "country":c, "sector":s
    }