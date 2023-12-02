import streamlit as st
import plotly
import json
import yaml
from pathlib import Path
from utils import get_connection
from utils import logo, print_object

logo()


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

configs = yaml.safe_load(Path('configs.yaml').read_text())
debug_mode = configs["debug_mode"]
market_indexes = configs["market_indexes"]
market_indexes = {k:v for list_item in market_indexes for (k,v) in list_item.items()}

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
    market_plots_[0:3]
)

tab_overview, = st.tabs(['overview'])
index_symbol = market_indexes[index]

if st.button('Launch'):
    if debug_mode:
        local_storage = configs["local_tmps_market_research"]
        conn = False
    else:
        conn = get_connection()
        local_storage = False
        
    with tab_overview:
        for plot_name in options:
            object = market_plots[plot_name]
            name = object['name']
            type_ = object['data_type']

            print_object(name, type_, index_symbol, debug_mode, local_storage, conn)
            
    
st.button("Re-run")