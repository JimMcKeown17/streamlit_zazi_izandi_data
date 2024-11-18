import streamlit as st
from display_24 import display_2024
from display_23 import display_2023
from display_home import display_home

st.set_page_config(layout="wide", page_title="ZZ Data Portal")


# Define your usernames and passwords
credentials = {
    'zazi': 'izandi'
}

# Function to handle login
def login():
    st.sidebar.header("Login")
    username = st.sidebar.text_input("Username", key="username")
    password = st.sidebar.text_input("Password", type="password", key="password")

    if st.sidebar.button("Login"):
        if username in credentials and credentials[username] == password:
            st.sidebar.success("Logged in as {}".format(username))
            st.session_state.user = username
            st.experimental_rerun()  # Rerun to update the sidebar with internal pages
        else:
            st.sidebar.error("Incorrect username or password")
            st.session_state.user = None
    st.sidebar.text("Log in for more detailed views.")

# option = st.sidebar.selectbox('Select a Year:', ('2024', '2023'))
# if option == "2024":
#     display_2024()
# elif option == "2023":
#     display_2023()

display_home()

# Show login section below the navigation
login()

# Logout button
if 'user' in st.session_state:
    if st.sidebar.button("Logout"):
        del st.session_state.user
        st.experimental_rerun()
else:
    st.warning("Please use sidebar for detailed analyses. Data is anonymized to protect schools & children. You may log in to access all data and de-anonymize names.")

st.sidebar.markdown("---")
st.sidebar.markdown("[Visit Zazi iZandi Website](http://zazi-izandi.co.za)")

