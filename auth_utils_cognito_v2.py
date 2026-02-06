import boto3
import streamlit as st
import boto3

import hmac
import hashlib
import base64


cognito_client = boto3.client('cognito-idp', region_name='eu-west-3')

def get_secret_hash(username):
    msg = username + st.secrets["CLIENT_ID"]
    dig = hmac.new(str(st.secrets["CLIENT_SECRET"]).encode('utf-8'), 
        msg = str(msg).encode('utf-8'), digestmod=hashlib.sha256).digest()
    d2 = base64.b64encode(dig).decode()
    return d2

def authenticate_user(username, password):
    try:
        response = cognito_client.initiate_auth(
            ClientId=st.secrets["CLIENT_ID"],
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={'USERNAME': username, 'PASSWORD': password, "SECRET_HASH": get_secret_hash(username)}
            )
    
        if response:
            # getting user group
            response_user_group = cognito_client.admin_list_groups_for_user(
                Username = username,
                UserPoolId = st.secrets["USER_POOL_ID"],
                Limit=2,
            )
            user_group =[x["GroupName"] for x in response_user_group["Groups"]][0]
            st.write(f"welcome: {username}")
            st.write(f"you are: {user_group}")
            return user_group
        
    except cognito_client.exceptions.NotAuthorizedException:
        st.error("Invalid username or password.")
    except Exception as e:
        st.error(str(e)) # type: ignore

def verify_auth_code(username, auth_code):
    try:
        response = cognito_client.confirm_sign_up(
            ClientId=st.secrets["CLIENT_ID"],
            SecretHash=get_secret_hash(username),
            Username=username,
            ConfirmationCode=auth_code,
            ForceAliasCreation=False,
        )
        if response:
            return response
    except cognito_client.exceptions.CodeMismatchException:
        st.error("Invalid auth code")
        return False
    except cognito_client.exceptions.ExpiredCodeException:
        st.error("user is already verified or expired code")
    except Exception as e:
        st.error(str(e))

def create_user(username, password):
    try:
        response = cognito_client.sign_up(
            ClientId=st.secrets["CLIENT_ID"],
            SecretHash=get_secret_hash(username),
            Username=username,
            Password=password,)
        
        _ = cognito_client.admin_add_user_to_group(
            UserPoolId=st.secrets["USER_POOL_ID"],
            Username=username,
            GroupName='guest'
        )
        return response["UserConfirmed"]
    except cognito_client.exceptions.UsernameExistsException:
            st.error("user already exists :(")
    except Exception as e:
            st.error(str(e))

def auth_code_forgot_password(username):
    try:
        response = cognito_client.forgot_password(
            ClientId=st.secrets["CLIENT_ID"],
            SecretHash=get_secret_hash(username),
            Username=username,
        )
        if response:
            return response
    except Exception as e:
        st.error(str(e))
        return False


def reset_password(username, new_password, auth_code):
    try:
        response = cognito_client.confirm_forgot_password(
            ClientId=st.secrets["CLIENT_ID"],
            SecretHash=get_secret_hash(username),
            Username=username,
            ConfirmationCode=auth_code,
            Password=new_password
        )
        if response:
            return response
    except Exception as e:
        st.error(str(e))
        return False
    
def delete_user(username):
    try:
        response = cognito_client.admin_delete_user(
                UserPoolId=st.secrets["USER_POOL_ID"],
                Username=username
            )
        if response.get("ResponseMetadata").get("HTTPStatusCode") == 200:
            st.write(f"Successfully deleted user: {username}")
            
    except Exception as e:
        st.error(str(e))
    

def _logout():
    """Log out the current user."""
    st.session_state.clear()
    st.success("You have been logged out successfully.")
    st.rerun()

def _authenticated_menu():
    st.sidebar.page_link("welcome_home.py", label="Home", icon="🏡")
    if st.session_state.role == 'superadmin':
        st.sidebar.page_link("pages/asset_explore.py", label="Explore assets")
        st.sidebar.page_link("pages/asset_deep_dive.py", label="Deep dive")
        st.sidebar.page_link("pages/markets.py", label="Markets")
        st.sidebar.page_link("pages/multiple_symbols.py", label="Batches")
        st.sidebar.page_link("pages/portfolio_dive.py", label="Portfolio")
    elif st.session_state.role == 'guest':
        st.sidebar.page_link("pages/portfolio_dive.py", label="Portfolio")
        st.sidebar.page_link("pages/asset_explore.py", label="Explore assets")
    st.sidebar.page_link("pages/delete_user.py", label="unsuscribe")

    if st.sidebar.button("Logout"):
        _logout()

def _unauthenticated_menu():
    # Show a navigation menu for unauthenticated users
    pass

def menu():
    _authenticated_menu()

def submenu():
    # Determine if a user is logged in or not, then show the correct
    if not st.session_state.get("authenticated"):
        _unauthenticated_menu()
        st.stop()
    else:
        st.switch_page("welcome_home.py")
        _authenticated_menu()

def menu_with_redirect():
    # Redirect users to the main page if not logged in, otherwise continue to
    # render the navigation menu
    try:
        if st.session_state.authenticated == True:
            _authenticated_menu()
    except:
        st.switch_page("welcome_home.py")
        submenu()
