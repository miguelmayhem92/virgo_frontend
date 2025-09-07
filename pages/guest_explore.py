import streamlit as st
import yaml
from pathlib import Path
import datetime

from utils import logo
from auth_utils_cognito import menu_with_redirect

configs = yaml.safe_load(Path('configs.yaml').read_text())
debug_mode = configs["debug_mode"]
models_dict = configs["models"]
execution_date = datetime.datetime.today().strftime('%Y-%m-%d')
execution_date = f"{execution_date}"
bucket = 'virgo-data'

st.set_page_config(layout="wide")
logo(debug_mode)
menu_with_redirect()

st.markdown("# Explore assets as guest")

st.write(
    """
    Here you will find analysis of the historical asset closing prices
    
    In this page you have thre tabs:
    - **overview** here you have a global view of the signals and hidden markov states of chosen asset
    - **backtest** explore the statitical properties of the signals
    - **edges** explore current edges using machine learning models

    Note that the plots can take about 5 seconds to load the data
    """
)

symbol_name = st.text_input('Asset symbol', 'PEP')