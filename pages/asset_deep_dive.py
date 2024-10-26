import streamlit as st
import yaml
from pathlib import Path
from utils import get_connection, execute_asset_lambda, execute_edgemodel_lambda, call_edge_json
import datetime
import pandas as pd
import boto3
import time 
from io import BytesIO

from virgo_modules.src.re_utils import produce_plotly_plots, produce_signals
from virgo_modules.src.ticketer_source import  analyse_index
from virgo_modules.src.backtester import SignalAnalyserObject
from virgo_modules.src.edge_utils.edge_utils import edge_probas_lines
from virgo_modules.src.edge_utils.conformal_utils import edge_conformal_lines
from virgo_modules.src.edge_utils.shap_utils import edge_shap_lines

from utils import logo, reading_last_execution, dowload_any_object, signal_position_message
from utils import perf_metrics_message, get_categorical_targets

from auth_utils import menu_with_redirect

configs = yaml.safe_load(Path('configs.yaml').read_text())
debug_mode = configs["debug_mode"]
asset_plots = configs["asset_plots"]
execution_date = datetime.datetime.today().strftime('%Y-%m-%d')
execution_date = f"{execution_date}"
bucket = 'virgo-data'

st.set_page_config(layout="wide")
logo(debug_mode)
menu_with_redirect()

st.markdown("# Asset deep-dive")

st.write(
    """
    Here you will find analysis of the historical asset closing prices
    
    In this page you have thre tabs:
    - **overview** here you have a global view of the signals and hidden markov states of chosen asset
    - **signal back-test** explore the statitical properties of the signals
    - **market risk** get a quick understanding of the market exposure risk of the asset in the current time and historically (soon)

    Note that the plots can take about 5 seconds to load the data
    some examples: AAPL(Apple), AMZN (Amazon), UBI.PA (Ubisoft), etc
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

st.markdown(""" 
For backtesting:
""")

high_exit = st.number_input('high exit:', max_value = 10, min_value=0, value= 5)
low_exit = st.number_input('low exit:', max_value = 10, min_value=0, value= 5)

late_opening = st.slider('late opening:', max_value = 10, min_value=0, value= 0)
late_opening = False if late_opening == 0 else late_opening

st.write(
    """
    select edge options
    """
)

on_edge = st.toggle('Activate edge model')
if on_edge:
    edge_threshold = st.slider('Edge threshold',30, 100, 40)/100
    conformal = st.checkbox("Conformal prediction")
    explain = st.checkbox("Explain")

on_market_risk = st.toggle('Activate market risk')
if on_market_risk:
    market_indexes = configs["market_indexes"]
    market_indexes = {k:v for list_item in market_indexes for (k,v) in list_item.items() if v != '^VIX'}
    market_indexes_ = ['DEFAULT'] + list(market_indexes.keys())
    market_index = st.selectbox(
        'select one option',
        tuple(market_indexes_)
    )
    inv_market_indexes = {v:k for k,v in market_indexes.items()}

exit_params = {
    'high_exit': float(high_exit),
    'low_exit': -float(low_exit)
}

models_dict = configs["models"]
models_descriptions = {k:v for list_item in models_dict for (k,v) in list_item.items()}

signals_dict = configs['signals']
signals_map = {k:v for list_item in signals_dict for (k,v) in list_item.items()}
signals = list(signals_map.keys())

tab_overview, tab_signal, tab_edge, tab_market_risk = st.tabs(['overview', 'signal back-test', 'edge analysis', 'market risk'])

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
        
        def asset_lambda_execution(symbol_name):
            payload = {'asset' : symbol_name}
            execute_asset_lambda(payload)
    
        try:
            aws_report_date = reading_last_execution('execution.json', f'market_plots/{symbol_name}/', 'ExecutionDate')
        except:
            asset_lambda_execution(symbol_name)
            aws_report_date = reading_last_execution('execution.json', f'market_plots/{symbol_name}/', 'ExecutionDate')

        print(f"execution_date: {execution_date}")
        print(f"aws_report_date: {aws_report_date}")
        if execution_date != aws_report_date:
            ## lambda execution if no available json 
            asset_lambda_execution(symbol_name)
            
        data_frame = dowload_any_object('dataframe.csv', f'market_plots/{symbol_name}/', 'csv',bucket)
        t_matrix = dowload_any_object('tmatrix.txt', f'market_plots/{symbol_name}/', 'txt', bucket)
        data_configs = dowload_any_object('asset_configs.json', f'market_plots/{symbol_name}/', 'json',bucket)

        with tab_overview:
            plotter = produce_plotly_plots(symbol_name, data_frame,data_configs,save_path = False,save_aws = False,show_plot = False, return_figs = True)
            for plot_name in options:
                
                if plot_name == "panel signals":
                    features_ = ['volatility_log_return', 'rel_MA_spread', 'target_mean_dow','pair_z_score','RSI','ROC','STOCHOSC']
                    spread_column = 'relative_spread_ma'
                    fig = plotter.plot_asset_signals(features_, spread_column ,date_intervals = False, look_back = 750)
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
        with tab_signal:
            for signal in signals: 
                sao = SignalAnalyserObject(data_frame, symbol_name, signal,test_size = 250, signal_position = late_opening, save_path = False, save_aws = False,
                                            show_plot = False, aws_credentials = False, return_fig = True)      
                st.subheader(f"{signals_map[signal]} - analysis and backtest", divider='rainbow')
                try:
                    fig = sao.signal_analyser(days_list = [7,15,30])
                    st.pyplot(fig)
                except:
                    st.write("no plot available :(")
                try:
                    fig2, json_messages = sao.create_backtest_signal(days_strategy = 30, **exit_params, open_in_list=['down','up'])
                    current_signal_position = signal_position_message(data_frame, signal)
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
                    payload = {
                        'asset': symbol_name,
                        'conformal': True,
                        'interpret': True,
                    }
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
                    time.sleep(3)
                    model_name = 'sirius'
                    edge_name = 'sirius_edge'
                    csv_name = f'{model_name}_{symbol_name}_edges.csv'
                    target_variables = ['target_down','target_up']
                    label_prediction = ['proba_'+x for x in target_variables]

                    data_frame['Date'] = pd.to_datetime(data_frame['Date'])

                    probas = dowload_any_object(csv_name, f'edge_models/{model_name}/{symbol_name}/', 'csv', bucket)
                    probas['Date'] = pd.to_datetime(probas['Date'])
                    edge_signals = produce_signals(probas, edge_name, edge_threshold, label_prediction)
                    new_signal_list = ['Date','proba_target_down','proba_target_up',f'signal_up_{model_name}_edge',f'acc_up_{model_name}_edge',f'signal_low_{model_name}_edge',f'acc_low_{model_name}_edge']
                    data_frame_edge = data_frame.merge(edge_signals[new_signal_list], on = 'Date', how = 'left')
                    sao = SignalAnalyserObject(data_frame_edge, symbol_name, edge_name,test_size = 250, signal_position = late_opening, save_path = False, save_aws = False,
                                            show_plot = False, aws_credentials = False, return_fig = True)  
                    fig = sao.signal_analyser(days_list = [7,15,30])
                    st.pyplot(fig)

                except:
                    st.write("no data available :(")

                try:
                    call_edge_json(file_name = 'current_edge.json', conn = conn, dict_keys = ['probability go down','probability go up'],
                                streamlit_conn = streamlit_conn, bucket = bucket, folder_path = f'edge_models/sirius/{symbol_name}/')
                except:
                    st.write("no message available :(")
                try:
                    fig2, json_messages = sao.create_backtest_signal(days_strategy = 30, **exit_params, open_in_list=['down','up'])
                    current_signal_position = signal_position_message(data_frame, signal)
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
                    data_frame_edge = get_categorical_targets(data_frame_edge, **target_params_up)
                    data_frame_edge = data_frame_edge.drop(columns = ['target_down']).rename(columns = {'target_up':'target_up_save'})
                    data_frame_edge = get_categorical_targets(data_frame_edge,**target_params_down)
                    data_frame_edge = data_frame_edge.drop(columns = ['target_up']).rename(columns = {'target_up_save':'target_up'})
                    perf_message = perf_metrics_message(data = data_frame_edge, test_data_size = 250, edge_name = edge_name)
                    st.write(perf_message)
                except:
                    st.write("no plot available :(")

                try:
                    if not conformal:
                        plot = edge_probas_lines(data = data_frame_edge, threshold = edge_threshold, look_back = 500)
                        st.plotly_chart(plot , use_container_width=True)
                    if conformal:
                        csv_name = f'{model_name}_{symbol_name}_conformal.csv'
                        conf_df = dowload_any_object(csv_name, f'edge_models/{model_name}/{symbol_name}/', 'csv', bucket)
                        fig = edge_conformal_lines(conf_df, [0.25,0.50,0.75], threshold=edge_threshold)
                        st.plotly_chart(fig , use_container_width=True)
                    if explain:
                        csv_name = f'{model_name}_{symbol_name}_shap.csv'
                        df_shap = dowload_any_object(csv_name, f'edge_models/{model_name}/{symbol_name}/', 'csv', bucket)
                        st.markdown('#### exaplainer:')
                        fig = edge_shap_lines(data=df_shap.drop(columns = ['Unnamed: 0']))
                        st.plotly_chart(fig , use_container_width=True)
                except:
                    st.write("no plot available :(")
        with tab_market_risk:
            if on_market_risk:
                my_error = False
                if market_index == 'DEFAULT':
                    try:
                        market_betas = dowload_any_object(file_name = 'betas_market.csv', folder = 'market_betas/', file_type = 'csv', bucket = 'virgo-data').iloc[:,1:]
                        asset_beta = market_betas[market_betas.asset == symbol_name].sort_values('rank')
                        market_index_symbol = asset_beta[asset_beta['rank'] == 1].market_index.values[0]
                    except:
                        my_error = 'no best beta available :(, use another option'
                else:
                    market_index_symbol = market_indexes[market_index]
                if not my_error:
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
                else:
                    st.write(my_error)


st.button("Re-run")
