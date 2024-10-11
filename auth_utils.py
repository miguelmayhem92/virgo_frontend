import streamlit as st
import hmac
from st_pages import hide_pages

def _check_password():
    """Authenticate user and manage login state."""
    if st.session_state.get("authenticated"):
        return True

    with st.form("Credentials"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log in")

    if submitted:
        if username in st.secrets["passwords"] and hmac.compare_digest(
            password,
            st.secrets.passwords[username],
        ):
            st.session_state.authenticated = True
            st.session_state.username = username
            st.session_state.role = st.secrets.roles.get(username, "user")  # Default to "user" if role not specified
            st.rerun()
        else:
            st.error("User not known or password incorrect.")

    return False


def _authenticated_menu():
    st.sidebar.page_link("hello_world.py", label="Home", icon="🏡")
    st.sidebar.page_link("pages/asset_explore.py", label="Explore assets")
    if st.session_state.role == 'admin':
        st.sidebar.page_link("pages/asset_deep_dive.py", label="Deep dive")
        st.sidebar.page_link("pages/markets.py", label="Markets")
        st.sidebar.page_link("pages/multiple_symbols.py", label="Batches")
    if st.sidebar.button("Logout"):
        _logout()


def _unauthenticated_menu():
    # Show a navigation menu for unauthenticated users
    pass

def _logout():
    """Log out the current user."""
    st.session_state.clear()
    st.success("You have been logged out successfully.")
    st.rerun()


def menu():
    # Determine if a user is logged in or not, then show the correct
    if not _check_password():
        _unauthenticated_menu()
        st.stop()
    else:
        _authenticated_menu()


def menu_with_redirect():
    # Redirect users to the main page if not logged in, otherwise continue to
    # render the navigation menu
    if not _check_password():
        st.switch_page("hello_world.py")
        # st.warning('loging please', icon="⚠️")
    menu()