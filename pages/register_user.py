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

st.write("## Register")

username = st.text_input("Username")
password = st.text_input("Password", type="password")
if st.button('register'):
    confirmation = create_user(username, password)
    if confirmation == False:
        st.write("A verification code was sent to the email address")
    else:
        st.error("user is already registered from streamlit")

if st.button('verify user'):
    st.switch_page("pages/verify_user.py")

if st.button('back home'):
    st.switch_page("welcome_home.py")