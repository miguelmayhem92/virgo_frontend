import time
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

def _check_password():
    """Authenticate user and manage login state."""
    if st.session_state.get("authenticated"):
        return True

    with st.form("Login Credentials"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log in")
    if submitted:
        user_group = authenticate_user(username, password)
        if user_group:
            st.session_state.authenticated = True
            st.session_state.username = username
            st.session_state.role = user_group
            st.rerun()
        else:
            st.error("User not known or password incorrect.")
    return False

def _register_new_user():

    with st.form("Signup Credentials"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("sign up")
    if submitted and username and password:
        confirmation = create_user(username, password)
        if confirmation == False:
            st.write("A verification code was sent to the email address")
            st.write("Now you can verify user in verification tab")
        else:
            st.error("user is already registered from streamlit")

def _verify_user():
    with st.form("verify user"):
         username = st.text_input("Username")
         auth_code = st.text_input("verification code")
         submitted_code = st.form_submit_button("verify")
    if submitted_code and username:
        virification = verify_auth_code(username, auth_code)
        if virification:
            st.write("user is verified")
            backhome = st.button("home")
            if backhome:
                st.rerun()

def _forgot_password():
    with st.form("forgot password"):
        username = st.text_input("Username")
        new_password = st.text_input("New Password", type="password")
        auth_code = st.text_input("Auth code")
        register = st.form_submit_button("Register password")
        if register:
            response= reset_password(username, new_password, auth_code)
            if response:
                st.write(f"new password is registered")
        submited = st.form_submit_button("Send auth code to email")
        if submited:
            response = auth_code_forgot_password(username)
            if response:
                st.write(f"an auth code was sent to {username}")
        
        
def _login_signup():
    with st.popover("Sign in"):
        activated = _check_password()
    with st.popover("Forgot password"):
        _forgot_password()
    with st.popover("Sign up"):
        _register_new_user()
    with st.popover("Verify user"):
        _verify_user()
    
    return activated

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
        st.sidebar.page_link("pages/guest_explore.py", label="Explore assets")
    elif st.session_state.role == 'guest':
        st.sidebar.page_link("pages/guest_explore.py", label="Explore assets")

    if st.sidebar.button("Logout"):
        _logout()

def _unauthenticated_menu():
    # Show a navigation menu for unauthenticated users
    pass

def menu():
    _authenticated_menu()

def submenu():
    # Determine if a user is logged in or not, then show the correct
    if not _login_signup():
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

    # if not _login_signup():
    #     st.switch_page("welcome_home.py")
    #     # st.warning('loging please', icon="⚠️")
    # menu()





# username = st.text_input("Username")
# password = st.text_input("Password", type="password")

# if st.button("Login"):
#     authenticate_user(username, password)

# username = st.text_input("Username_signup")
# password = st.text_input("Password_signup", type="password")

# if st.button("Signup"):
#      create_user(username, password)
# st.write("A verification email was sent")
# auth_code = st.text_input("verification code")
# if st.button("auth code"):
#     verify_auth_code(username, auth_code)




