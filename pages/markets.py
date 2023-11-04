import streamlit as st
import time
import numpy as np
import plotly.express as px
import plotly
from st_files_connection import FilesConnection

import json
import yaml
from pathlib import Path

st.set_page_config(page_title="Plotting Demo", page_icon="📈", layout="wide")


st.markdown("# Plotting Demo")
st.sidebar.header("Plotting Demo")
st.write(
    """This demo illustrates a combination of plotting and animation with
Streamlit. We're generating a bunch of random numbers in a loop for around
5 seconds. Enjoy!"""
)

debug_mode = False

configs = yaml.safe_load(Path('configs.yaml').read_text())
market_indexes = configs["market_indexes"]
tabs = st.tabs(market_indexes)

if debug_mode:
    for tab,index in zip(tabs,market_indexes):
        with tab:
            fig = plotly.io.read_json(f'C:/Users/Miguel/Dropbox/virgo/{index}/panel_signals.json')
            st.plotly_chart(fig, theme="streamlit", use_container_width=True)
else:
    for tab,index in zip(tabs,market_indexes):
        with tab:
            conn = st.connection('s3', type=FilesConnection)
            jsonfile = conn.read(f"virgo-data/market_plots/{index}/panel_signals.json", input_format="json")
            json_dump = json.dumps(jsonfile)
            fig = plotly.io.from_json(json_dump)
            st.plotly_chart(fig, theme="streamlit", use_container_width=True)

# Streamlit widgets automatically run the script from top to bottom. Since
# this button is not connected to any other logic, it just causes a plain
# rerun.
st.button("Re-run")