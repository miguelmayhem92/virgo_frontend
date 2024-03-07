import streamlit as st
import yaml
from pathlib import Path
import datetime
import boto3
from virgo_modules.src.re_utils import produce_simple_ts_from_model
from utils import logo, execute_edgemodel_lambda, reading_last_execution, s3_image_reader, aws_print_object, get_connection

configs = yaml.safe_load(Path('configs.yaml').read_text())
debug_mode = configs["debug_mode"]
models_dict = configs["models"]
execution_date = datetime.datetime.today().strftime('%Y-%m-%d')
execution_date = f"report date: {execution_date}"
bucket = 'virgo-data'

st.set_page_config(layout="wide")
logo(debug_mode)

st.markdown("# Explore assets")

st.write(
    """
    Here you will find analysis of the historical asset closing prices
    In this page you have thre tabs:
    - **overview** here you have a global view of the signals and hidden markov states of chosen asset
    - **edges** explore current edges using machine learning models

    Note that the plots can take about 5 seconds to load the data
    """
)

symbol_name = st.text_input('Asset symbol', 'PEP')

st.write(
    """
    select the arguments to configure the signals
    """
)

# args for the signal etl
roc_window = st.slider('ROC window',0, 50, 5)
rsi_window = st.slider('RSI window',0, 50, 5)
ma1_window = st.slider('MA short term',0, 50, 5)
ma2_window = st.slider('MA long term',0, 50, 15)
threshold = st.slider('Z threshold',0.0, 3.0, 2.0, 0.2)

tab_overview, tab_edge = st.tabs(['overview', 'edge analysis'])

feature_config_generic = {
    'ROC':{'method': 'roc_feature', 'config_params': {'threshold': threshold, 'window': roc_window}},
    'RSI':{'method': 'rsi_feature_improved', 'config_params': {'threshold': threshold, 'window': rsi_window}},
    'rel_MA_spread':{'method': 'relative_spread_MA', 'config_params': {'ma1': ma1_window, 'ma2': ma2_window, 'threshold': threshold}}
}

bucket = 'virgo-data'
models_descriptions = {k:v for list_item in models_dict for (k,v) in list_item.items()}


if st.button('Launch'):
    with st.spinner('.......................... Now loading ..........................'):
        with tab_overview:

            fig = produce_simple_ts_from_model(symbol_name, configs = feature_config_generic)
            st.plotly_chart(fig, use_container_width=True)

        with tab_edge:

            st.subheader(f"Sirius edge model - analysis and backtest", divider='rainbow')
            st.markdown(models_descriptions['sirius']['description'])

            conn = False
            streamlit_conn = False
            if not debug_mode:
                conn = get_connection()
                streamlit_conn = True

            def edgemodel_lambda_execution(symbol_name):
                payload = {"asset": symbol_name}
                execute_edgemodel_lambda(payload)

            try:
                aws_report_date = reading_last_execution('current_edge.json', f'edge_models/sirius/{symbol_name}/', 'ExecutionDate')
            except:
                edgemodel_lambda_execution(symbol_name)
                aws_report_date = reading_last_execution('current_edge.json', f'edge_models/sirius/{symbol_name}/', 'ExecutionDate')

            print(f"execution_date: {execution_date}")
            print(f"aws_report_date: {aws_report_date}")

            if execution_date != aws_report_date:
                ## lambda execution if no available json 
                edgemodel_lambda_execution(symbol_name)
            
            try:
                name = f'signals_strategy_distribution_sirius_edge.png'
                fig = s3_image_reader(bucket = "virgo-data",key = f"edge_models/sirius/{symbol_name}/{name}")
                st.image(fig)
            except:
                st.write("no plot available :(")

            try:
                name = str(f'signals_strategy_return_sirius_edge.json' )
                aws_print_object(file_name = name, type = 'message', streamlit_conn = streamlit_conn, conn = conn, bucket = bucket, folder_path = f'edge_models/sirius/{symbol_name}/')
            except:
                st.write("no plot available :(")

            try:
                name = f'signals_strategy_return_sirius_edge.png'
                fig = s3_image_reader(bucket = "virgo-data",key = f"edge_models/sirius/{symbol_name}/{name}")
                st.image(fig)
            except:
                st.write("no plot available :(")

st.button("Re-run")