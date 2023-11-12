import streamlit as st
import plotly
import json
import yaml
from pathlib import Path
from utils import get_connection, s3_image_reader
from PIL import Image

import pandas as pd

st.set_page_config(page_title="Plotting Demo", page_icon="📈", layout="wide")

st.markdown("# Plotting Demo")
st.sidebar.header("Plotting Demo")
st.write(
    """This virgo demo illustrates a combination of plotting and animation with
Streamlit. We're generating a bunch of random numbers in a loop for around
5 seconds. Enjoy!"""
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
    asset_plots_[0:2]
)

signals = configs['signals']

tab_overview, tab_signal, tab_market = st.tabs(['overview', 'signal back-test', 'market risk'])

if st.button('Launch'):
    name = f'signals_strategy_return_RSI.png'
    # conn = get_connection()
    # file_stream = conn.read(f"virgo-data/market_plots/{symbol_name}/{name}", input_format="png", ttl=30)
    # fig = Image.open(file_stream)
    fig = s3_image_reader(bucket = "virgo-data",key = f"market_plots/{symbol_name}/{name}")
    st.image(fig)


if st.button('Launch'):
    if debug_mode:
        local_storage = configs["local_tmps_asset_research"]
    else:
        conn = get_connection()

    with tab_overview:
        try:
            if debug_mode:
                market_message = json.load(open(f'{local_storage}/{symbol_name}/market_message.json'))
            else:
                market_message = conn.read(f"virgo-data/market_plots/{symbol_name}/market_message.json", input_format="json", ttl=30)

            message1 = market_message['current_state']
            message2 = market_message['current_step_state']
            message3 = market_message['report_date']
            st.write(f"status:")
            st.write(f"{message1}")
            st.write(f"{message2}")
            st.write(f"{message3}")
        except:
            st.write("no text was recorded :(")
        for plot_name in options:
            name = asset_plots[plot_name]
            try:
                if debug_mode:
                    fig = plotly.io.read_json(f'{local_storage}/{symbol_name}/{name}')
                else:
                    jsonfile = conn.read(f"virgo-data/market_plots/{symbol_name}/{name}", input_format="json", ttl=30)
                    json_dump = json.dumps(jsonfile)
                    fig = plotly.io.from_json(json_dump)

                st.plotly_chart(fig, theme="streamlit", use_container_width=True)
            except:
                st.write("no plot available :(")

        with tab_signal:
            for signal in signals:
                st.write(f"{signal}")
                try:
                    name = f'signals_strategy_distribution_{signal}.png'
                    if debug_mode:
                        fig = Image.open(f'{local_storage}/{symbol_name}/{name}')
                    else:
                        file_stream = conn.read(f"virgo-data/market_plots/{symbol_name}/{name}", input_format="png", ttl=30)
                        fig = Image.open(file_stream)
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
                        file_stream = conn.read(f"virgo-data/market_plots/{symbol_name}/{name}", input_format="png", ttl=30)
                        fig = Image.open(file_stream)
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
                    file_stream = conn.read(f"virgo-data/market_plots/{symbol_name}/{name}", input_format="png", ttl=30)
                    fig = Image.open(file_stream)
                st.image(fig)
            except:
                st.write("no plot available :(")
  
st.button("Re-run")