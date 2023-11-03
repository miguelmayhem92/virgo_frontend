import streamlit as st
import time
import numpy as np
import plotly.express as px
import plotly
from st_files_connection import FilesConnection

import json
import re

st.set_page_config(page_title="Plotting Demo", page_icon="📈", layout="wide")


st.markdown("# Plotting Demo")
st.sidebar.header("Plotting Demo")
st.write(
    """This demo illustrates a combination of plotting and animation with
Streamlit. We're generating a bunch of random numbers in a loop for around
5 seconds. Enjoy!"""
)

df = px.data.gapminder()

fig = px.scatter(
    df.query("year==2007"),
    x="gdpPercap",
    y="lifeExp",
    size="pop",
    color="continent",
    hover_name="country",
    log_x=True,
    size_max=60,
)

tab1, tab2, tab3 = st.tabs(["Streamlit theme (default)", "Plotly native theme", "test html"])
with tab1:
    # Use the Streamlit theme.
    # This is the default. So you can also omit the theme argument.
    st.plotly_chart(fig, theme="streamlit", use_container_width=True)
with tab2:
    # Use the native Plotly theme.
    st.plotly_chart(fig, theme="streamlit", use_container_width=True)

#with tab3:
    
#    fig = plotly.io.read_json('C:/Users/Miguel/Dropbox/virgo/^GSPC/panel_signals.json')
#    st.plotly_chart(fig, theme="streamlit", use_container_width=True)

with tab3:
    conn = st.connection('s3', type=FilesConnection)
    jsonfile = conn.read("virgo-data/panel_signals.json", input_format="json")
    json_dump = json.dumps(jsonfile)
    fig = plotly.io.from_json(json_dump)
    st.plotly_chart(fig, theme="streamlit", use_container_width=True)
    

# Streamlit widgets automatically run the script from top to bottom. Since
# this button is not connected to any other logic, it just causes a plain
# rerun.
st.button("Re-run")