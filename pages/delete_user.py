import streamlit as st
from auth_utils_cognito_v2 import delete_user

st.write("# Welcome to Virgo! 📈")

st.markdown(
    """
    Virgo is an statistical arbitrage app that is meant to mine investing oportunities in financial markets. 
    Virgo uses advanced statistical techniques and machine learning that help people to take better investment decisions.
    :mechanical_arm:
"""
)

st.write("## Delete user")

username = st.text_input("Username")
confirm_delete = st.toggle('confirm?')
if confirm_delete and st.button('delete user'):
    delete_user(username)
    st.session_state.clear()
    st.rerun()

if st.button('back home'):
    st.switch_page("welcome_home.py")