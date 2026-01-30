import time
import streamlit as st
from auth_utils_cognito_v2 import create_user, verify_auth_code

st.write("# Welcome to Virgo! 📈")

st.markdown(
    """
    Virgo is an statistical arbitrage app that is meant to mine investing oportunities in financial markets. 
    Virgo uses advanced statistical techniques and machine learning that help people to take better investment decisions.
    :mechanical_arm:
"""
)

st.write("## Verify")

username = st.text_input("Username")
verification_code = st.text_input("verification code")

if st.button('verify'):
    virification = verify_auth_code(username, verification_code)
    if virification:
        st.write("user is verified, then redirecting")
        time.sleep(3)
        st.switch_page("welcome_home.py")
    else:
        st.write("user is not verified")

if st.button('back home'):
    st.switch_page("welcome_home.py")