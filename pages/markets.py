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

tabs = st.tabs(['overview'])
index_symbol = market_indexes[index]

if st.button('Launch'):
    if debug_mode:
        local_storage = configs["local_tmps_market_research"]
        for tab in tabs:
            with tab:
                try:
                    with open(f'{local_storage}/{index_symbol}/market_message.json') as json_file:
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
                    name = market_plots[plot_name]
                    try:
                        fig = plotly.io.read_json(f'{local_storage}/{index_symbol}/{name}')
                        st.plotly_chart(fig, theme="streamlit", use_container_width=True)
                    except:
                        st.write("no plot available :(")
    else:
        for tab in tabs:
            with tab:
                conn = get_connection()
                try:
                    market_message = conn.read(f"virgo-data/market_plots/{index_symbol}/market_message.json", input_format="json", ttl=30)
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
                    name = market_plots[plot_name]
                    try:
                        jsonfile = conn.read(f"virgo-data/market_plots/{index_symbol}/{name}", input_format="json", ttl=30)
                        json_dump = json.dumps(jsonfile)
                        fig = plotly.io.from_json(json_dump)
                        st.plotly_chart(fig, theme="streamlit", use_container_width=True)
                    except:
                        st.write("no plot available :(")

# Streamlit widgets automatically run the script from top to bottom. Since
# this button is not connected to any other logic, it just causes a plain
# rerun.
st.button("Re-run")