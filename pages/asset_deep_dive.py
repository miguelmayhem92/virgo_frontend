import streamlit as st
import yaml
from pathlib import Path
from utils import get_connection, execute_asset_lambda
import datetime
import pandas as pd
import boto3
import time 
from io import BytesIO

from virgo_modules.src.re_utils import produce_plotly_plots
from virgo_modules.src.ticketer_source import signal_analyser_object

from utils import logo, reading_last_execution, dowload_any_object

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

tab_overview, tab_signal= st.tabs(['overview', 'signal back-test'])

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
            payload = {"asset": symbol_name}
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
                    features_ = ['volatility_log_return','z_log_return', 'rel_MA_spread', 'target_mean_dow','pair_z_score','RSI']
                    spread_column = 'relative_spread_ma'
                    fig = plotter.plot_asset_signals(features_, spread_column ,date_intervals = False)
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
            sao = signal_analyser_object(data_frame, symbol_name, save_path = False, save_aws = False, show_plot = False, aws_credentials = False, return_fig = True)
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

st.button("Re-run")
