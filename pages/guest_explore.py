import streamlit as st
import yaml
import pandas as pd
from pathlib import Path
import datetime
import boto3
import time
from io import BytesIO
from virgo_modules.src.re_utils import produce_simple_ts_from_model, produce_signals
from virgo_modules.src.edge_utils.edge_utils import edge_probas_lines, get_rolling_probs
from virgo_modules.src.ticketer_source import  analyse_index
from virgo_modules.src.backtester import SignalAnalyserObject
from virgo_modules.src.market.market_tools import MarketAnalysis
from virgo_modules.src.ticketer_source import stock_eda_panel
from virgo_modules.src.re_utils import produce_plotly_plots

from utils import logo, execute_edgemodel_lambda, reading_last_execution, get_connection, call_edge_json, dowload_any_object, signal_position_message
from utils import perf_metrics_message, get_categorical_targets
from auth_utils_cognito import menu_with_redirect

configs = yaml.safe_load(Path('configs.yaml').read_text())
debug_mode = configs["debug_mode"]
models_dict = configs["models"]
execution_date = datetime.datetime.today().strftime('%Y-%m-%d')
execution_date = f"{execution_date}"
bucket = 'virgo-data'
guest_symbols = configs["guest_symbols"]
guest_symbols = {k:v for list_item in guest_symbols for (k,v) in list_item.items()}
guest_symbol_map = configs["guest_symbol_map"]
guest_symbol_map = {k:v for list_item in guest_symbol_map for (k,v) in list_item.items()}

st.set_page_config(layout="wide")
logo(debug_mode)
menu_with_redirect()

st.markdown("# Explore assets as guest")

st.write(
    """
    Here you will find analysis of the historical asset closing prices
    
    In this page you have thre tabs:
    - **overview** here you have a global view of the signals and hidden markov states of chosen asset
    - **backtest** explore the statitical properties of the signals
    - **edges** explore current edges using machine learning models

    Note that the plots can take about 5 seconds to load the data
    And note that as guest you have limited access
    """
)
symbols_ = list(guest_symbols.keys())
symbol_name_ = st.selectbox(
    'select one option',
    tuple(symbols_)
)
symbol_name = guest_symbols[symbol_name_]
symbol_type = guest_symbol_map.get(symbol_name_, "normal")

market_plots = configs["market_plots"]
market_plots = {k:v for list_item in market_plots for (k,v) in list_item.items()}
market_plots_ = list(market_plots.keys())
options = market_plots_[0:4]

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
    smooth_windown = st.slider('Smooth window',1, 30, 3)
on_market_risk = st.toggle('Activate market risk')
if on_market_risk:
    market_indexes = configs["market_indexes"]
    market_indexes = {k:v for list_item in market_indexes for (k,v) in list_item.items() if v != '^VIX'}
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
            if symbol_type == "normal":
                fig,df = produce_simple_ts_from_model(symbol_name, configs = feature_config_generic, n_days = 900)
                st.plotly_chart(fig, use_container_width=True)
            elif symbol_type == "market":

                time.sleep(2)
                if debug_mode:
                    local_storage = False
                    conn = False
                    streamlit_conn = False
                else:
                    conn = get_connection()
                    local_storage = False
                    streamlit_conn = True
                
                data_frame = dowload_any_object('dataframe.csv', f'market_plots/{symbol_name}/', 'csv',bucket)
                t_matrix = dowload_any_object('tmatrix.txt', f'market_plots/{symbol_name}/', 'txt', bucket)
                data_configs = dowload_any_object('asset_configs.json', f'market_plots/{symbol_name}/', 'json',bucket)
                forecastings = dowload_any_object('batch_predictions_csv.csv', f'market_plots/{symbol_name}/', 'csv',bucket)

                plotter = produce_plotly_plots(symbol_name, data_frame,data_configs,save_path = False,save_aws = False,show_plot = False, return_figs = True)

                for plot_name in options:

                    # object = market_plots[plot_name]
                    # name = object['name']
                    # type_ = object['data_type']
                    # method = object['method']

                    # print_object(name, type_, index_symbol, debug_mode, local_storage, conn)

                    if plot_name == "panel signals":
                        features_ = ['volatility_log_return', 'rel_MA_spread', 'target_mean_dow','pair_z_score','RSI','ROC','STOCHOSC']
                        spread_column = 'relative_spread_ma'
                        fig = plotter.plot_asset_signals(features_, spread_column ,date_intervals = False, look_back=1000)
                        st.plotly_chart(fig, use_container_width=True)

                    elif plot_name == "current state":
                        _,jsnom = plotter.plot_hmm_analysis(settings = data_configs, t_matrix = t_matrix)
                        st.write(jsnom)

                    elif plot_name == 'states analysis':
                        fig,_ = plotter.plot_hmm_analysis(settings = data_configs, t_matrix = t_matrix)
                        st.plotly_chart(fig, use_container_width=True)
                        
                    elif plot_name == "states scaled time series":
                        fig = plotter.explore_states_ts()
                        st.plotly_chart(fig, use_container_width=True)
                    
                    elif plot_name == "forecastings":
                        fig = plotter.produce_forecasting_plot(forecastings)
                        st.plotly_chart(fig, use_container_width=True)

        with tab_backtest:
            if symbol_type == "normal":
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
            if symbol_type == "normal":
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
                        plot = get_rolling_probs(data=data_frame, window=smooth_windown,look_back=700)
                        st.plotly_chart(plot , use_container_width=True)
                    except:
                        st.write("no plot available :(")

        with market_risk_tab:
            if symbol_type == "normal":
                if on_market_risk:
                    market_symbols = list(inv_market_indexes.keys())
                    object_stock = stock_eda_panel(symbol_name , 3500, '15y')
                    object_stock.get_data()
                    object_stock.volatility_analysis(lags = 3, trad_days = 15, window_log_return = 10, plot = False, save_features = False)
                    feat_list = list()
                    for symbol in market_symbols:
                        simple_name = inv_market_indexes.get(symbol)
                        feat_name = simple_name + "_return"
                        object_stock.extract_sec_data(symbol, ["Date","Close"], {"Close":simple_name})
                        object_stock.lag_log_return(lags = 3, feature=simple_name, feature_name=feat_name)
                        feat_list.append(feat_name)
                    ma = MarketAnalysis(object_stock.df, feat_list, "log_return")
                    general_report, current_report, figure = ma.compute_general_report(sample_size=20, offset=5, index=False, subsample_ts=500, show_plot=False)
                    st.write("the market analysis uses multiple market indexes and robust linear regression to get beta")
                    st.write("general report")
                    st.dataframe(general_report)
                    st.write("latest report")
                    st.dataframe(current_report)
                    st.write("visualizations")
                    st.pyplot(figure)



st.button("Re-run")