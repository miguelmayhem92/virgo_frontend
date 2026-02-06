import streamlit as st
import plotly
import json
import yaml
from pathlib import Path
from utils import get_connection
from utils import logo
import time
from auth_utils_cognito_v2 import menu_with_redirect

configs = yaml.safe_load(Path('configs.yaml').read_text())
debug_mode = configs["debug_mode"]
multi_symbols = configs["multi_symbols"]
multi_symbols_sirius = configs["multi_symbols_sirius"]

st.set_page_config(layout="wide")
logo(debug_mode)
menu_with_redirect()

st.markdown("# Multiple assets")

st.write(
     """
    Here you can explore some rankings and investment possibilities
    you have three lits:
    - top low, it a list of low momentum assets
    - down tickers are the assets that have persisting negative returns
    - and in-market, my current portfolio
    
    Note that the plots can take about 5 seconds to load the data
    """
)


multi_symbol_selection = st.selectbox(
    'select one option',
    tuple(multi_symbols)
)
if multi_symbol_selection == "sirius":
    prefix = "{type_asset}-"
    sirius_options = [x.replace(prefix,"") for x in multi_symbols_sirius]
    multi_symbols_sirius_selection = st.selectbox(
        'select one option',
        tuple(sirius_options)
    )
    option = st.selectbox(
        "sirius modules have some options",
        ("asset", "etf", "crypto")
    )
    option = prefix.format(type_asset = option)
    multi_symbol_selection = f"{option}{multi_symbols_sirius_selection}"
    print(multi_symbol_selection)
tabs = st.tabs(['dashboard'])

if st.button('Launch'):
    with st.spinner('.......................... Now loading ..........................'):
        time.sleep(2)

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