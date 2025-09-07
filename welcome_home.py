import streamlit as st
from utils import logo
# from auth_utils import menu, menu_with_redirect
from auth_utils_cognito import menu
from pathlib import Path
import yaml
from st_pages import  get_nav_from_toml

configs = yaml.safe_load(Path('configs.yaml').read_text())
debug_mode = configs["debug_mode"]

st.set_page_config(layout="wide")
logo(debug_mode)
try:
    if st.session_state.authenticated == True:
        menu()
except:
    st.switch_page("pages/virgo_signin.py")
    

st.write("# Welcome to Virgo! 📈")

st.markdown(
    """
    Virgo is an statistical arbitrage app that is meant to mine investing oportunities in financial markets. 
    Virgo uses advanced statistical techniques and machine learning that help people to take better investment decisions.
    **👈 Select a functionality from the sidebar** and see what Virgo can do :mechanical_arm:
    ### Motivation
    - **95%** of the independent investors loss money and quit the market because of bad practices:
        - lack of risk assessment
        - follow the emotions
        - lack of strategy
        - or follow unrealistic strategies
        - lack of backtested strategies (at least to built some confidence and strategy understanding)
    ### The functionalities:
    - **Explore Asset** exaplore any asset and experiment with signals, get backtested results and edges using ML models
    - **Deep Dive** explore signals, trends, and other statical prperties of your favorite assets (Markov hidden models, strategy backtest, market risk)
    - **Markets** get a view of the most important market indexes. Also get some analysis thanks to signals, market forecasting and Markov hidden states
    - **Recomendations** explore in a dashboard possible investment candidates thanks to signal processing

"""
)