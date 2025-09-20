import streamlit as st
from utils import logo
# from auth_utils import menu
from auth_utils_cognito import submenu
from pathlib import Path
import yaml
from st_pages import  get_nav_from_toml

configs = yaml.safe_load(Path('configs.yaml').read_text())
debug_mode = configs["debug_mode"]

st.set_page_config(layout="wide")
logo(debug_mode)

st.write("# Welcome to Virgo! 📈")

st.write("## Login or register")

st.text("Virgo is an statistical arbitrage app that is meant to mine investing oportunities in financial markets.")

submenu()