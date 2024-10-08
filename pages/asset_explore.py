import streamlit as st
import yaml
import pandas as pd
from pathlib import Path
import datetime
import boto3
from io import BytesIO
from virgo_modules.src.re_utils import produce_simple_ts_from_model, edge_probas_lines, produce_signals
from virgo_modules.src.ticketer_source import  analyse_index
from virgo_modules.src.backtester import SignalAnalyserObject
from utils import logo, execute_edgemodel_lambda, reading_last_execution, get_connection, call_edge_json, dowload_any_object, signal_position_message
from utils import perf_metrics_message, get_categorical_targets

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
if on_edge:
    edge_threshold = st.slider('Edge threshold',30, 100, 40)/100

on_market_risk = st.toggle('Activate market risk')
if on_market_risk:
    market_indexes = configs["market_indexes"]
    market_indexes = {k:v for list_item in market_indexes for (k,v) in list_item.items() if v != '^VIX'}
    market_indexes_ = list(market_indexes.keys())
    market_index = st.selectbox(
        'select one option',
        tuple(market_indexes_)
    )
    inv_market_indexes = {v:k for k,v in market_indexes.items()}

tab_overview,tab_backtest, tab_edge, market_risk_tab = st.tabs(['overview', 'backtest signal', 'edge analysis', 'market risk'])

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

exit_strategy = {
    'high_exit': 5,
    'low_exit': -4
}

bucket = 'virgo-data'
models_descriptions = {k:v for list_item in models_dict for (k,v) in list_item.items()}
signals = list(feature_config_generic.keys())

if st.button('Launch'):
    with st.spinner('.......................... Now loading ..........................'):
        with tab_overview:

            fig,df = produce_simple_ts_from_model(symbol_name, configs = feature_config_generic, n_days = 1500)
            st.plotly_chart(fig, use_container_width=True)

        with tab_backtest:
            for signal in signals:   
                sao = SignalAnalyserObject(df, symbol_name, signal,test_size = 250, save_path = False, save_aws = False,
                                            show_plot = False, aws_credentials = False, return_fig = True)   
                st.subheader(f"{signals_map[signal]} - analysis and backtest", divider='rainbow')
                # try:
                fig = sao.signal_analyser(days_list = [7,15,30])
                st.pyplot(fig)
                # except:
                #     st.write("no plot available :(")
                try:
                    fig2, json_messages = sao.create_backtest_signal(days_strategy = 30, **exit_strategy, open_in_list=['down','up'])
                    current_signal_position = signal_position_message(df, signal)
                    json_messages.append(current_signal_position)
                    st.write(json_messages)
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
                
                # try:
                model_name = 'sirius'
                edge_name = 'sirius_edge'
                csv_name = f'{model_name}_{symbol_name}_edges.csv'
                target_variables = ['target_down','target_up']
                label_prediction = ['proba_'+x for x in target_variables]
                
                probas = dowload_any_object(csv_name, f'edge_models/{model_name}/{symbol_name}/', 'csv', bucket)
                probas['Date'] = pd.to_datetime(probas['Date'])

                edge_signals = produce_signals(probas, edge_name, edge_threshold, label_prediction)

                new_signal_list = ['Date','proba_target_down','proba_target_up',f'signal_up_{model_name}_edge',f'acc_up_{model_name}_edge',f'signal_low_{model_name}_edge',f'acc_low_{model_name}_edge']
                data_frame = df.merge(edge_signals[new_signal_list], on = 'Date', how = 'left')

                sao = SignalAnalyserObject(data_frame, symbol_name, edge_name,test_size = 250, save_path = False, save_aws = False,
                                            show_plot = False, aws_credentials = False, return_fig = True)  
                fig = sao.signal_analyser(days_list = [7,15,30])
                st.pyplot(fig)

                # except:
                #     st.write("no data available :(")

                try:
                    call_edge_json(file_name = 'current_edge.json', conn = conn, dict_keys = ['probability go down','probability go up'],
                                streamlit_conn = streamlit_conn, bucket = bucket, folder_path = f'edge_models/sirius/{symbol_name}/')
                except:
                    st.write("no message available :(")
                try:
                    fig2, json_messages = sao.create_backtest_signal(days_strategy = 30, **exit_strategy, open_in_list=['down','up'])
                    current_signal_position = signal_position_message(df, signal)
                    json_messages.append(current_signal_position)
                    st.write(json_messages)
                    buf = BytesIO()
                    fig2.savefig(buf, format="png")
                    st.image(buf)

                    target_configs = {
                        'params_up': {'flor_loss': 0, 'horizon': 6, 'top_gain': 3},
                        'params_down': {'flor_loss': -4, 'horizon': 7, 'top_gain': 0}
                    }
                    target_params_up = target_configs['params_up']
                    target_params_down = target_configs['params_down']
                    data_frame = get_categorical_targets(data_frame, **target_params_up)
                    data_frame = data_frame.drop(columns = ['target_down']).rename(columns = {'target_up':'target_up_save'})
                    data_frame = get_categorical_targets(data_frame,**target_params_down)
                    data_frame = data_frame.drop(columns = ['target_up']).rename(columns = {'target_up_save':'target_up'})
                    perf_message = perf_metrics_message(data = data_frame, test_data_size = 250, edge_name = edge_name)
                    st.write(perf_message)
                except:
                    st.write("no plot available :(")

                try:
                    plot = edge_probas_lines(data = data_frame, threshold = edge_threshold, look_back = 500)
                    st.plotly_chart(plot , use_container_width=True)
                except:
                    st.write("no plot available :(")

        with market_risk_tab:
            if on_market_risk:
                market_index_symbol = market_indexes[market_index]

                lag = 2
                n_obs = 3500
                window_size = '15y'

                aiv = analyse_index(index_data = market_index_symbol, asset = symbol_name, n_obs = n_obs, lag = lag, data_window = window_size, return_fig = True, show_plot = False)
                aiv.process_data()
                fig = aiv.plot_betas(sample_size = 30, offset = 5, subsample_ts =False)
                st.pyplot(fig)

                aiv.get_betas(subsample_ts=30)
                betas_result = aiv.states_result

                for i,_ in enumerate(betas_result):
                    betas_result[i]['index'] = inv_market_indexes.get(betas_result[i]['index'])

                st.write(betas_result)
st.button("Re-run")