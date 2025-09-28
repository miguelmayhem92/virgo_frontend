from io import BytesIO
import yaml
import pandas as pd
from pathlib import Path
import seaborn as sns
import streamlit as st

from utils import logo
from auth_utils_cognito import menu_with_redirect

from virgo_modules.src.ticketer_source import stock_eda_panel
from tooling.portfolio_utils import return_matrix, filter_scale_ts

configs = yaml.safe_load(Path('configs.yaml').read_text())
debug_mode = configs["debug_mode"]

st.set_page_config(layout="wide")
logo(debug_mode)
menu_with_redirect()


st.markdown("# Portfolio dive")

st.write(
    """
    Some portfolio analysis
    """
)


symbol_name = st.text_input('Asset symbol', 'PEP,LMT')
tickers = symbol_name.split(",")
if st.button("add"):
    st.write(",".join(tickers))

lags_short = st.number_input('short term lag', 3)
lags_mid= st.number_input('mid term lag', 7)
trade_days = st.number_input('trading days', 7)
begin_date = st.text_input('Begin date', '2025-01-01')


if st.button("run"):
    stock_code = tickers[0]
    object_stock = stock_eda_panel(stock_code , 1000, '5y')
    object_stock.get_data()
    object_stock.df = object_stock.df[["Date","Close"]].rename(columns={"Close": stock_code})
    for code in tickers[1:]:
        object_stock.extract_sec_data(code, ["Date","Close"], {"Close":code})

    df_rets = return_matrix(object_stock.df, tickers, lags_short, apply_log=True)
    correlations = df_rets[tickers].corr(method="spearman")

    plot1 = sns.clustermap(correlations, method="complete", cmap='RdBu', annot=True, 
                annot_kws={"size": 9}, vmin=-1, vmax=1, figsize=(6,7))
    buf = BytesIO()
    plot1.savefig(buf, format="png")
    st.image(buf)

    df_rets = return_matrix(object_stock.df, tickers, lags_mid, apply_log=True)
    correlations = df_rets[tickers].corr(method="spearman")

    plot2 = sns.clustermap(correlations, method="complete", cmap='RdBu', annot=True, 
                annot_kws={"size": 9}, vmin=-1, vmax=1, figsize=(6,7))
    buf = BytesIO()
    plot2.savefig(buf, format="png")
    st.image(buf)

    # time series and volatility
    plot=filter_scale_ts(object_stock.df, begin_date, tickers,trad_days = trade_days,lags=lags_short)
    st.plotly_chart(plot, use_container_width=True)

