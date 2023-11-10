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
multi_symbols = configs["multi_symbols"]

multi_symbol_selection = st.selectbox(
    'select one option',
    tuple(multi_symbols)
)

tabs = st.tabs(['dashboard'])

if st.button('Launch'):
    if debug_mode:
        local_storage = configs["local_tmps"]
        for tab in tabs:
            with tab:
                try:
                    fig = plotly.io.read_json(f'{local_storage}/{multi_symbol_selection}.json')
                    st.plotly_chart(fig, theme="streamlit", use_container_width=True)
                except:
                    st.write("no plot available :(")
    else:
        for tab in tabs:
            with tab:
                conn = get_connection()
                try:
                    jsonfile = conn.read(f"virgo-data/multi_dashboards/{multi_symbol_selection}.json", input_format="json", ttl=30)
                    json_dump = json.dumps(jsonfile)
                    fig = plotly.io.from_json(json_dump)
                    st.plotly_chart(fig, theme="streamlit", use_container_width=True)
                except:
                    st.write("no plot available :(")

st.button("Re-run")