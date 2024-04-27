import streamlit as st
import plotly
import json
import yaml
from pathlib import Path
from utils import get_connection
from utils import logo, print_object, dowload_any_object, get_connection

from virgo_modules.src.re_utils import produce_plotly_plots
import time

configs = yaml.safe_load(Path('configs.yaml').read_text())
debug_mode = configs["debug_mode"]
market_indexes = configs["market_indexes"]
market_indexes = {k:v for list_item in market_indexes for (k,v) in list_item.items()}

st.set_page_config(layout="wide")
logo(debug_mode)

bucket = 'virgo-data'

st.markdown("# Markets analysis")

st.write(
    """
    Here you can explore the main market indexes such as S&P500 CAC40, etc
    some features of the analysis are:
    * signal time series visualization
    * hidden markov model analysis
    * and market forecasting
    
    Note that the plots can take about 5 seconds to load the data
    """
)


market_plots = configs["market_plots"]
market_plots = {k:v for list_item in market_plots for (k,v) in list_item.items()}

market_indexes_ = list(market_indexes.keys())
index = st.selectbox(
    'select one option',
    tuple(market_indexes_)
)

market_plots_ = list(market_plots.keys())
options = st.multiselect(
    'select you plot options',
    market_plots_,
    market_plots_[0:4]
)

tab_overview, = st.tabs(['overview'])
index_symbol = market_indexes[index]

# with st.spinner('Wait for it...'):
# st.success('Done!')

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
        
        data_frame = dowload_any_object('dataframe.csv', f'market_plots/{index_symbol}/', 'csv',bucket)
        t_matrix = dowload_any_object('tmatrix.txt', f'market_plots/{index_symbol}/', 'txt', bucket)
        data_configs = dowload_any_object('asset_configs.json', f'market_plots/{index_symbol}/', 'json',bucket)
        forecastings = dowload_any_object('batch_predictions_csv.csv', f'market_plots/{index_symbol}/', 'csv',bucket)

        plotter = produce_plotly_plots(index_symbol, data_frame,data_configs,save_path = False,save_aws = False,show_plot = False, return_figs = True)

        with tab_overview:

            for plot_name in options:

                # object = market_plots[plot_name]
                # name = object['name']
                # type_ = object['data_type']
                # method = object['method']

                # print_object(name, type_, index_symbol, debug_mode, local_storage, conn)

                if plot_name == "panel signals":
                    features_ = ['volatility_log_return', 'rel_MA_spread', 'target_mean_dow','pair_z_score','RSI','ROC','STOCHOSC']
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
                
                elif plot_name == "forecastings":
                    fig = plotter.produce_forecasting_plot(forecastings)
                    st.plotly_chart(fig, use_container_width=True)

                # features_ = ['volatility_log_return', 'rel_MA_spread','RSI']
                # spread_column = 'relative_spread_ma'
        
                # plotter = produce_plotly_plots(ticket_name, data_frame,settings, save_path, save_aws = save_aws, show_plot= False, aws_credentials = credentials)
                # plotter.produce_forecasting_plot(batch_predictions_csv)
                # plotter.plot_asset_signals(features_, spread_column)
                # plotter.explore_states_ts()
                # plotter.plot_hmm_analysis(settings = settings, t_matrix = t_matrix, model = model)

        
st.button("Re-run")