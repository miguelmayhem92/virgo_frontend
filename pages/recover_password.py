import streamlit as st
import time
from auth_utils_cognito_v2 import auth_code_forgot_password, reset_password

st.write("# Welcome to Virgo! 📈")

st.markdown(
    """
    Virgo is an statistical arbitrage app that is meant to mine investing oportunities in financial markets. 
    Virgo uses advanced statistical techniques and machine learning that help people to take better investment decisions.
    :mechanical_arm:
"""
)

st.write("## Recover password")

username = st.text_input("Username")
new_password = st.text_input("New Password", type="password")

if st.button('reset password'):
    response = auth_code_forgot_password(username)
    if response:
        st.write(f"an auth code was sent to {username}")

auth_code = st.text_input("Auth code")
if st.button('apply new password'):
    response= reset_password(username, new_password, auth_code)
    if response:
        st.write(f"new password is registered, redirecting")
        time.sleep(3)
        st.switch_page("welcome_home.py")
        
if st.button('back home'):
    st.switch_page("welcome_home.py")