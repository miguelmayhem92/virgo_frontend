import streamlit as st
import plotly
import json
import yaml
from pathlib import Path
from utils import get_connection

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

tabs = st.tabs(['overview'])

if st.button('Launch'):
    if debug_mode:
        local_storage = configs["local_tmps_asset_research"]
        for tab in tabs:
            with tab:
                try:
                    with open(f'{local_storage}/{symbol_name}/market_message.json') as json_file:
                        market_message = json.load(json_file)
                    message1 = market_message['current_state']
                    message2 = market_message['current_step_state']
                    message3 = market_message['report_date']
                    st.write(f"status:")
                    st.write(f"current state: {message1}")
                    st.write(f"current step in the state: {message2}")
                    st.write(f"report date: {message3}")
                except:
                    st.write("no text was recorded :(")
                for plot_name in options:
                    name = asset_plots[plot_name]
                    try:
                        fig = plotly.io.read_json(f'{local_storage}/{symbol_name}/{name}')
                        st.plotly_chart(fig, theme="streamlit", use_container_width=True)
                    except:
                        st.write("no plot available :(")
    else:
        for tab in tabs:
            with tab:
                conn = get_connection()
                try:
                    market_message = conn.read(f"virgo-data/market_plots/{symbol_name}market_message.json", input_format="json", ttl=30)
                    message1 = market_message['current_state']
                    message2 = market_message['current_step_state']
                    message3 = market_message['report_date']
                    st.write(f"status:")
                    st.write(f"current state: {message1}")
                    st.write(f"current step in the state: {message2}")
                    st.write(f"report date: {message3}")
                except:
                    st.write("no text was recorded :(")
                for plot_name in options:
                    name = asset_plots[plot_name]
                    try:
                        jsonfile = conn.read(f"virgo-data/market_plots/{symbol_name}/{name}", input_format="json", ttl=30)
                        json_dump = json.dumps(jsonfile)
                        fig = plotly.io.from_json(json_dump)
                        st.plotly_chart(fig, theme="streamlit", use_container_width=True)
                    except:
                        st.write("no plot available :(")

# Streamlit widgets automatically run the script from top to bottom. Since
# this button is not connected to any other logic, it just causes a plain
# rerun.
st.button("Re-run")