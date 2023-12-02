import streamlit as st
from utils import logo


logo()

st.write("# Welcome to Virgo! 📈")

st.markdown(
    """
    Virgo is an statistical arbitrage app that is meant to mine investing oportunities in financial markets. 
    Virgo uses advanced statistical techniques and machine learning that help people to take better investment decisions.
    **👈 Select a functionality from the sidebar** and see what Virgo can do :mechanical_arm:
    ### The functionalities:
    - **Asset deep dive** explore signals, trends, and other statical prperties of your favorite assets (Markov hidden models, strategy backtest, market risk)
    - **Markets** get a view of the most important market indexes. Also get some analysis thanks to signals, market forecasting and Markov hidden states
    - **multiple symbols** explore in a dashboard possible investment candidates thanks to signal processing

"""
)