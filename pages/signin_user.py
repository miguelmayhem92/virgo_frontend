import streamlit as st
from auth_utils_cognito_v2 import authenticate_user

st.write("# Welcome to Virgo! 📈")

st.markdown(
    """
    Virgo is an statistical arbitrage app that is meant to mine investing oportunities in financial markets. 
    Virgo uses advanced statistical techniques and machine learning that help people to take better investment decisions.
    :mechanical_arm:
"""
)

st.write("## Login")

username = st.text_input("Username")
password = st.text_input("Password", type="password")
if st.button('login'):
    user_group = authenticate_user(username, password)
    if user_group:
        st.session_state.authenticated = True
        st.session_state.username = username
        st.session_state.role = user_group
        st.switch_page("welcome_home.py")
        st.rerun()
    else:
        st.error("User not known or password incorrect.")

if st.button('forgot password'):
    st.switch_page("pages/recover_password.py")

if st.button('back home'):
    st.switch_page("welcome_home.py")