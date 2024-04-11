import streamlit as st
import yaml
import pandas as pd
from pathlib import Path
import datetime
import boto3
from io import BytesIO
from virgo_modules.src.re_utils import produce_simple_ts_from_model, edge_probas_lines
from virgo_modules.src.ticketer_source import signal_analyser_object
from utils import logo, execute_edgemodel_lambda, reading_last_execution, get_connection, call_edge_json, dowload_any_object

configs = yaml.safe_load(Path('configs.yaml').read_text())
debug_mode = configs["debug_mode"]
models_dict = configs["models"]
execution_date = datetime.datetime.today().strftime('%Y-%m-%d')
execution_date = f"{execution_date}"
bucket = 'virgo-data'

st.set_page_config(layout="wide")
logo(debug_mode)

st.markdown("# Explore assets")

st.write(
    """
    Here you will find analysis of the historical asset closing prices
    
    In this page you have thre tabs:
    - **overview** here you have a global view of the signals and hidden markov states of chosen asset
    - **backtest** explore the statitical properties of the signals
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

st.write(
    """
    select edge options
    """
)

on_edge = st.toggle('Activate edge model')
edge_threshold = st.slider('Edge threshold',30, 100, 40)/100

tab_overview,tab_backtest, tab_edge = st.tabs(['overview', 'backtest signal', 'edge analysis'])

feature_config_generic = {
    'ROC':{'method': 'roc_feature', 'config_params': {'threshold': threshold, 'window': roc_window}},
    'RSI':{'method': 'rsi_feature_improved', 'config_params': {'threshold': threshold, 'window': rsi_window}},
    'rel_MA_spread':{'method': 'relative_spread_MA', 'config_params': {'ma1': ma1_window, 'ma2': ma2_window, 'threshold': threshold}}
}
signals_map = {
    'ROC':'ROC',
    'RSI':'RSI',
    'rel_MA_spread': "Moving Averages"
}

bucket = 'virgo-data'
models_descriptions = {k:v for list_item in models_dict for (k,v) in list_item.items()}
signals = list(feature_config_generic.keys())

if st.button('Launch'):
    with st.spinner('.......................... Now loading ..........................'):
        with tab_overview:

            fig,df = produce_simple_ts_from_model(symbol_name, configs = feature_config_generic)
            st.plotly_chart(fig, use_container_width=True)

        with tab_backtest:
            sao = signal_analyser_object(df, symbol_name, save_path = False, save_aws = False, show_plot = False, aws_credentials = False, return_fig = True)
            for signal in signals:      
                st.subheader(f"{signals_map[signal]} - analysis and backtest", divider='rainbow')
                # try:
                fig = sao.signal_analyser(test_size = 250, feature_name = signal, days_list = [7,15,30], threshold = 0.05,verbose = False)
                st.pyplot(fig)
                # except:
                #     st.write("no plot available :(")
                try:
                    fig2, json_message = sao.create_backtest_signal(days_strategy = 30, test_size = 250, feature_name = signal)
                    st.write(json_message)
                    buf = BytesIO()
                    fig2.savefig(buf, format="png")
                    st.image(buf)
                except:
                    st.write("no plot available :(")

        with tab_edge:
            if on_edge:
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
                    model_name = 'sirius'
                    edge_name = 'sirius_edge'
                    csv_name = f'{model_name}_{symbol_name}_edges.csv'
                    edge_signals = dowload_any_object(csv_name, f'edge_models/{model_name}/{symbol_name}/', 'csv',bucket)
                    # edge_signals['Date'] = pd.to_datetime(edge_signals['Date'], format='mixed',utc=True).dt.date
                    edge_signals['Date'] = pd.to_datetime(edge_signals['Date'])

                    new_signal_list = ['Date','proba_target_down','proba_target_up',f'signal_up_{model_name}_edge',f'acc_up_{model_name}_edge',f'signal_low_{model_name}_edge',f'acc_low_{model_name}_edge']
                    data_frame = df.merge(edge_signals[new_signal_list], on = 'Date', how = 'left')

                    sao = signal_analyser_object(data_frame, symbol_name, save_path = False, save_aws = False, show_plot = False, aws_credentials = False, return_fig = True)

                    fig = sao.signal_analyser(test_size = 250, feature_name = edge_name, days_list = [7,15,30], threshold = 0.05,verbose = False)
                    st.pyplot(fig)

                except:
                    st.write("no data available :(")

                try:
                    call_edge_json(file_name = 'current_edge.json', conn = conn, dict_keys = ['probability go down','probability go up'],
                                streamlit_conn = streamlit_conn, bucket = bucket, folder_path = f'edge_models/sirius/{symbol_name}/')
                except:
                    st.write("no message available :(")
                try:
                    exit_strategy = {
                        'high_exit': 5,
                        'low_exit': -4
                    }
                    fig2, json_message = sao.create_backtest_signal(days_strategy = 30, test_size = 250, feature_name = edge_name, **exit_strategy)
                    st.write(json_message)
                    buf = BytesIO()
                    fig2.savefig(buf, format="png")
                    st.image(buf)
                except:
                    st.write("no plot available :(")

                try:
                    plot = edge_probas_lines(data = data_frame, threshold = edge_threshold)
                    st.plotly_chart(plot , use_container_width=True)
                except:
                    st.write("no plot available :(")


st.button("Re-run")