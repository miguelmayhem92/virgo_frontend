import streamlit as st
import plotly
import json
import yaml
from pathlib import Path
from utils import get_connection, s3_image_reader
from PIL import Image

import pandas as pd

from utils import logo, print_object

logo()

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

configs = yaml.safe_load(Path('configs.yaml').read_text())
debug_mode = configs["debug_mode"]
asset_plots = configs["asset_plots"]

asset_plots = {k:v for list_item in asset_plots for (k,v) in list_item.items()}

symbol_name = st.text_input('Asset symbol', 'PEP')

asset_plots_ = list(asset_plots.keys())
options = st.multiselect(
    'select you plot options',
    asset_plots_,
    asset_plots_[0:3]
)

signals = configs['signals']

tab_overview, tab_signal, tab_market = st.tabs(['overview', 'signal back-test', 'market risk'])

if st.button('Launch'):
    if debug_mode:
        local_storage = configs["local_tmps_asset_research"]
        conn = False
    else:
        conn = get_connection()
        local_storage = False

    with tab_overview:
        for plot_name in options:
            object = asset_plots[plot_name]
            name = object['name']
            type_ = object['data_type']

            print_object(name, type_, symbol_name, debug_mode, local_storage, conn)
            
    with tab_signal:
        for signal in signals:
            st.write(f"{signal}")
            try:
                name = f'signals_strategy_distribution_{signal}.png'
                if debug_mode:
                    fig = Image.open(f'{local_storage}/{symbol_name}/{name}')
                else:
                    fig = s3_image_reader(bucket = "virgo-data",key = f"market_plots/{symbol_name}/{name}")
                st.image(fig)
            except:
                st.write("no plot available :(")
            try:
                name = str(f'signals_strategy_return_{signal}.json' )
                if debug_mode:
                    message = json.load(open(f'{local_storage}/{symbol_name}/{name}'))
                else:
                    message = conn.read(f"virgo-data/market_plots/{symbol_name}/{name}", input_format="json", ttl=30)
                message1 = message['benchmark']
                message2 = message['strategy']
                st.write(f"{message1}")
                st.write(f"{message2}")
            except:
                st.write("no plot available :(")
            try:
                name = f'signals_strategy_return_{signal}.png'
                if debug_mode:
                    fig = Image.open(f'{local_storage}/{symbol_name}/{name}')
                else:
                    fig = s3_image_reader(bucket = "virgo-data",key = f"market_plots/{symbol_name}/{name}")
                st.image(fig)
            except:
                st.write("no plot available :(")

    with tab_market:
        st.write(f"best fit market index")
        try:
            name = 'market_best_fit.csv'
            if debug_mode:
                df = pd.read_csv(f'{local_storage}/{symbol_name}/{name}')
            else:
                df = conn.read(f"virgo-data/market_plots/{symbol_name}/{name}", input_format="csv", ttl=30)
            st.dataframe(df)
        except:
            st.write("no plot available :(")
        try:
            name = f'market_best_fit.png' 
            if debug_mode:
                fig = Image.open(f'{local_storage}/{symbol_name}/{name}')
            else:
                fig = s3_image_reader(bucket = "virgo-data",key = f"market_plots/{symbol_name}/{name}")
            st.image(fig)
        except:
            st.write("no plot available :(")

st.button("Re-run")