import streamlit as st
import plotly
import json
import yaml
from pathlib import Path
from utils import get_connection, s3_image_reader, execute_asset_lambda
from PIL import Image
import datetime
import pandas as pd
import boto3
import time 

from utils import logo, print_object

configs = yaml.safe_load(Path('configs.yaml').read_text())
debug_mode = configs["debug_mode"]
asset_plots = configs["asset_plots"]
execution_date = datetime.datetime.today().strftime('%Y-%m-%d')
execution_date = f"report date: {execution_date}"
bucket = 'virgo-data'

st.set_page_config(layout="wide")
logo(debug_mode)

st.markdown("# Asset deep-dive")

st.write(
    """
    Here you will find analysis of the historical asset closing prices
    In this page you have thre tabs:
    - **overview** here you have a global view of the signals and hidden markov states of chosen asset
    - **signal back-test** explore the statitical properties of the signals
    - **market risk** get a quick understanding of the market exposure risk of the asset in the current time and historically 

    Note that the plots can take about 5 seconds to load the data
    """
)

asset_plots = {k:v for list_item in asset_plots for (k,v) in list_item.items()}
symbol_name = st.text_input('Asset symbol', 'PEP')

asset_plots_ = list(asset_plots.keys())
options = st.multiselect(
    'select you plot options',
    asset_plots_,
    asset_plots_[0:3]
)

signals_dict = configs['signals']
signals_map = {k:v for list_item in signals_dict for (k,v) in list_item.items()}
signals = list(signals_map.keys())

tab_overview, tab_signal, tab_market = st.tabs(['overview', 'signal back-test', 'market risk'])

if st.button('Launch'):
    with st.spinner('.......................... Now loading ..........................'):
        time.sleep(2)

        if debug_mode:
            local_storage = False
            conn = False
            streamlit_conn = False
        else:
            conn = get_connection()
            local_storage = False
            streamlit_conn = True

        def reading_last_execution():
            name = "market_message.json" 
            session = boto3.Session(
                                aws_access_key_id=st.secrets['AWS_ACCESS_KEY_ID'],
                                aws_secret_access_key=st.secrets['AWS_SECRET_ACCESS_KEY'])
            s3_resource = session.resource('s3')
            bucket = s3_resource.Bucket('virgo-data')
            image = bucket.Object(f"market_plots/{symbol_name}/{name}")
            jsonfile = image.get().get('Body').read().decode()
            market_message = json.loads(jsonfile)
            aws_report_date = market_message['report_date']
            return aws_report_date
        
        def asset_lambda_execution(symbol_name):
            payload = {"asset": symbol_name}
            execute_asset_lambda(payload)
            

        try:
            aws_report_date = reading_last_execution()
        except:
            asset_lambda_execution(symbol_name)
            aws_report_date = reading_last_execution()

        print(f"execution_date: {execution_date}")
        print(f"aws_report_date: {aws_report_date}")
        if execution_date != aws_report_date:
            ## lambda execution if no available json 
            asset_lambda_execution(symbol_name)
            

        with tab_overview:
            for plot_name in options:
                object = asset_plots[plot_name]
                name = object['name']
                type_ = object['data_type']
                if debug_mode:
                    print_object(name, type_, symbol_name, False, local_storage, conn, streamlit_conn, bucket)
                else:
                    print_object(name, type_, symbol_name, False, local_storage, conn, streamlit_conn, bucket)

        with tab_signal:
            for signal in signals:
                maped_signal = signals         
                st.subheader(f"{signals_map[signal]} - analysis and backtest", divider='rainbow')
                try:
                    name = f'signals_strategy_distribution_{signal}.png'
                    fig = s3_image_reader(bucket = "virgo-data",key = f"market_plots/{symbol_name}/{name}")
                    st.image(fig)
                except:
                    st.write("no plot available :(")
                try:
                    name = str(f'signals_strategy_return_{signal}.json' )

                    if debug_mode:
                        print_object(name, "message", symbol_name, False, local_storage, conn, streamlit_conn, bucket)
                    else:
                        print_object(name, "message", symbol_name, False, local_storage, conn, streamlit_conn, bucket)

                except:
                    st.write("no plot available :(")
                try:
                    name = f'signals_strategy_return_{signal}.png'
                    fig = s3_image_reader(bucket = "virgo-data",key = f"market_plots/{symbol_name}/{name}")
                    st.image(fig)
                except:
                    st.write("no plot available :(")

        with tab_market:
            st.write(f"best fit market index")
            try:
                name = 'market_best_fit.csv'

                if debug_mode:
                    print_object(name, "csv", symbol_name, False, local_storage, conn, streamlit_conn, bucket)
                else:
                    print_object(name, "csv", symbol_name, False, local_storage, conn, streamlit_conn, bucket)

            except:
                st.write("no plot available :(")
            try:
                name = f'market_best_fit.png' 
                fig = s3_image_reader(bucket = "virgo-data",key = f"market_plots/{symbol_name}/{name}")
                st.image(fig)
            except:
                st.write("no plot available :(")

st.button("Re-run")













# if st.button('Launch'):
#     if debug_mode:
#         local_storage = configs["local_tmps_asset_research"]
#         conn = False
#     else:
#         conn = get_connection()
#         local_storage = False

#     ### lambda execution
#     name = "market_message.json" 
#     try:
#         if debug_mode:
#             market_message = json.load(open(f'{local_storage}/{symbol_name}/{name}'))
#         else:
#             market_message = conn.read(f"virgo-data/market_plots/{symbol_name}/{name}", input_format="json", ttl=30)
#         aws_report_date = market_message['report_date']
#     except:
#         ## lambda execution if no available json 
#         lambda_client = boto3.client('lambda')
#         payload = {"asset": symbol_name}
#         result = execute_lambda(lambda_client, asset_lambda, json.dumps(payload))
#         print('lambda status code: ', result['StatusCode'])
#     ## retry
#     if debug_mode:
#             market_message = json.load(open(f'{local_storage}/{symbol_name}/{name}'))
#     else:
#         market_message = conn.read(f"virgo-data/market_plots/{symbol_name}/{name}", input_format="json", ttl=30)
#     aws_report_date = market_message['report_date']
    
#     if execution_date != aws_report_date:
#         ## lambda execution if no available json 
#         lambda_client = boto3.client('lambda')
#         payload = {"asset": symbol_name}
#         result = execute_lambda(lambda_client, asset_lambda, json.dumps(payload))
#         print('lambda status code: ', result['StatusCode'])


#     with tab_overview:
#         for plot_name in options:
#             object = asset_plots[plot_name]
#             name = object['name']
#             type_ = object['data_type']

#             print_object(name, type_, symbol_name, debug_mode, local_storage, conn)
            
#     with tab_signal:
#         for signal in signals:
#             st.write(f"{signal}")
#             try:
#                 name = f'signals_strategy_distribution_{signal}.png'
#                 if debug_mode:
#                     fig = Image.open(f'{local_storage}/{symbol_name}/{name}')
#                 else:
#                     fig = s3_image_reader(bucket = "virgo-data",key = f"market_plots/{symbol_name}/{name}")
#                 st.image(fig)
#             except:
#                 st.write("no plot available :(")
#             try:
#                 name = str(f'signals_strategy_return_{signal}.json' )
#                 if debug_mode:
#                     message = json.load(open(f'{local_storage}/{symbol_name}/{name}'))
#                 else:
#                     message = conn.read(f"virgo-data/market_plots/{symbol_name}/{name}", input_format="json", ttl=30)
#                 message1 = message['benchmark']
#                 message2 = message['strategy']
#                 st.write(f"{message1}")
#                 st.write(f"{message2}")
#             except:
#                 st.write("no plot available :(")
#             try:
#                 name = f'signals_strategy_return_{signal}.png'
#                 if debug_mode:
#                     fig = Image.open(f'{local_storage}/{symbol_name}/{name}')
#                 else:
#                     fig = s3_image_reader(bucket = "virgo-data",key = f"market_plots/{symbol_name}/{name}")
#                 st.image(fig)
#             except:
#                 st.write("no plot available :(")

#     with tab_market:
#         st.write(f"best fit market index")
#         try:
#             name = 'market_best_fit.csv'
#             if debug_mode:
#                 df = pd.read_csv(f'{local_storage}/{symbol_name}/{name}')
#             else:
#                 df = conn.read(f"virgo-data/market_plots/{symbol_name}/{name}", input_format="csv", ttl=30)
#             st.dataframe(df)
#         except:
#             st.write("no plot available :(")
#         try:
#             name = f'market_best_fit.png' 
#             if debug_mode:
#                 fig = Image.open(f'{local_storage}/{symbol_name}/{name}')
#             else:
#                 fig = s3_image_reader(bucket = "virgo-data",key = f"market_plots/{symbol_name}/{name}")
#             st.image(fig)
#         except:
#             st.write("no plot available :(")

# st.button("Re-run")