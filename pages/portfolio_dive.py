from io import BytesIO
import datetime
from dateutil.relativedelta import relativedelta
from PIL import Image
import yaml
import time

import pandas as pd
from pathlib import Path
import seaborn as sns
import streamlit as st
import matplotlib.pyplot as plt
from utils import logo, execute_state_machine_allocator, dowload_any_object, find_info
from auth_utils_cognito_v2 import menu_with_redirect

from virgo_modules.src.ticketer_source import stock_eda_panel
from tooling.portfolio_utils import return_matrix, filter_scale_ts
from tooling.portfolio_utils import (
    asset_to_color, 
    sirius_in_allocator_plot,
    plot_ts_allocations, 
    pie_plots_candidates, 
    pie_plots_benchmarks, 
    sirius_summary_plot
)

configs = yaml.safe_load(Path('configs.yaml').read_text())
debug_mode = configs["debug_mode"]
bucket = 'virgo-data'
EXECUTE_AFTER = 2
targets = ["optimal_asset_future_return","optimal_bench1_future_return","optimal_bench2_future_return","optimal_bench3_future_return",
        "optimal_bench4_future_return","optimal_bench5_future_return"]
map_targets = {
    "proba_target_down":"proba_go_up",
    "proba_target_up":"proba_go_down",
}
guest_symbols = configs["guest_symbols"]
guest_symbols = {k:v for list_item in guest_symbols for (k,v) in list_item.items()}
guest_symbol_map = configs["guest_symbol_map"]
guest_symbol_map = {k:v for list_item in guest_symbol_map for (k,v) in list_item.items()}

st.set_page_config(layout="wide")
logo(debug_mode)
menu_with_redirect()


st.markdown("# Portfolio dive")

st.write(
    """
    Decorrelate assets, get allocation and calculate probability to go up or down
    """
)
if st.session_state.role == 'guest':
    symbols_ = list(guest_symbols.keys())
    st.write(
        f"""
        select one from the list:
        """
    )  
    st.write(guest_symbols)

symbol_name = st.text_input('Asset symbol', 'PEP,LMT')
tickers = symbol_name.split(",")
tickers = [x.strip() for x in tickers]

def inspect(asset_list, guest_symbols):
    rejected = list()
    for x in asset_list:
        if x not in guest_symbols.values():
            rejected.append(x)
    if len(rejected)>0:
        rejected_str = ",".join(rejected)
        st.write(f"rejected symbols: {rejected_str}")
    asset_list = [x for x in asset_list if x not in rejected]
    return asset_list


if st.button("add"):
    if st.session_state.role == 'guest':
        tickers = inspect(tickers, guest_symbols)
    str_asset_list = ",".join(tickers)
    st.write(f"selected assets: {str_asset_list}")

lags_short = st.number_input('short term lag', 3)
lags_mid= st.number_input('mid term lag', 7)
trade_days = st.number_input('trading days', 7)

date_back = datetime.datetime.now() - relativedelta(days=100)
date_back_str = date_back.strftime("%Y-%m-%d")
begin_date = st.text_input('Begin date', date_back_str)

on_allocator = st.toggle('Activate allocator model')

tab_overview, allocation, sirius = st.tabs(['overview',"allocation", "sirius"])

if st.button("run"):
    with st.spinner('.......................... Now loading ..........................'):
        with tab_overview:
            if len(tickers) < 2:
                st.error("the list must be higher than 1 items")

            info_collect = list()
            for s in tickers:
                info = find_info(s)
                info_collect.append(info)
            info_collect_df = pd.DataFrame(info_collect)
            st.write("### General Info:")
            st.dataframe(info_collect_df)
            
            stock_code = tickers[0]
            object_stock = stock_eda_panel(stock_code , 1000, '5y')
            object_stock.get_data()
            object_stock.df = object_stock.df[["Date","Close"]].rename(columns={"Close": stock_code})
            for code in tickers[1:]:
                try:
                    object_stock.extract_sec_data(code, ["Date","Close"], {"Close":code})
                except:
                    st.error(f"{code} not found")
            st.write("### Correlograms:")
            df_rets = return_matrix(object_stock.df, tickers, lags_short, apply_log=True)
            correlations = df_rets[tickers].corr(method="spearman")

            plot1 = sns.clustermap(correlations, method="complete", cmap='RdBu', annot=True, 
                        annot_kws={"size": 9}, vmin=-1, vmax=1, figsize=(6,7))
            buf1 = BytesIO()
            plot1.savefig(buf1, format="png")

            df_rets = return_matrix(object_stock.df, tickers, lags_mid, apply_log=True)
            correlations = df_rets[tickers].corr(method="spearman")

            plot2 = sns.clustermap(correlations, method="complete", cmap='RdBu', annot=True, 
                        annot_kws={"size": 9}, vmin=-1, vmax=1, figsize=(6,7))
            buf2 = BytesIO()
            plot2.savefig(buf2, format="png")

            f, ax = plt.subplots(1,2)
            buf1.seek(0)
            im = Image.open(buf1)
            ax[0].imshow(im)
            ax[0].grid(False)
            ax[0].set_xticks([])
            ax[0].set_yticks([])
            ax[0].set_title(f"correlogram for {lags_short} lags", fontsize=5)
            buf2.seek(0)
            im = Image.open(buf2)
            ax[1].imshow(im)
            ax[1].grid(False)
            ax[1].set_xticks([])
            ax[1].set_yticks([])
            ax[1].set_title(f"correlogram for {lags_mid} lags", fontsize=5)
            st.pyplot(f)


            # time series and volatility
            plot=filter_scale_ts(object_stock.df, begin_date, tickers,trad_days = trade_days,lags=lags_short)
            st.plotly_chart(plot, use_container_width=True)
            succcess_main_page = True

        with allocation:
            if on_allocator and succcess_main_page:
                allocator_name = "_".join(tickers) + "_andromeda_edges.csv"
                sirius_name = "_".join(tickers) + "_sirius_edges.csv"
                folder_concat = "_".join(tickers)

                def get_execution_time():
                    try:
                        execution = dowload_any_object("time_execution.json", f'edge_models/andromeda/consolidate/{folder_concat}/', 'json', bucket)
                        execution_time_str = execution.get("execution_time") # str
                        execution_time = datetime.datetime.strptime(execution_time_str, '%Y-%m-%d:%H:%M:%S')
                        current_execution_time = datetime.datetime.now()
                        elapsed_time = current_execution_time - execution_time
                        hours_elapsed = divmod(elapsed_time.total_seconds(), 60*60)[0]
                        return hours_elapsed
                    except:
                        hours_elapsed=24
                        return hours_elapsed
                
                hours_elapsed = get_execution_time()
               
                if hours_elapsed > EXECUTE_AFTER:
                    print("launch step machine")
                    execute_state_machine_allocator({"asset_list":tickers})
                for i in range(10):
                    hours_elapsed = get_execution_time()
                    if hours_elapsed > EXECUTE_AFTER:
                        time.sleep(15)
                        print(f"waiting stepmachine to finish {i}, {hours_elapsed}")
                        continue
                    else:
                        print("done! step machine finished")
                        allocator_df = dowload_any_object(allocator_name, f'edge_models/andromeda/consolidate/', 'csv', bucket)
                        sirius_df = dowload_any_object(sirius_name, f'edge_models/andromeda/consolidate/', 'csv', bucket)
                        break
                # producing dashboards!!!
                asset2color = asset_to_color(tickers, targets)
                fig1 = pie_plots_candidates(allocator_df, tickers,asset2color)
                fig2 = pie_plots_benchmarks(allocator_df, targets, asset2color)
                fig3 = plot_ts_allocations(allocator_df,tickers, targets, asset2color)
                st.write("""
                    The allocation shows suggestion of how much to invest in an asset given some benchmarks:
                    * the benchmarks are a group of indexes that are weakly correlated but that are robust in terms of return and volatility
                    * then we have the candidate asset that we are interested to find the allocation percentage given the bench marks
                         
                    The allocation model will find the expected allocation individually in the asset list, creating portfolios per asset vs benchmarks
                    Then the results are ranked in the pie plots
                         
                    Then we have:
                    * expected: the expected allocation 
                    * observed and past: PAST optimal allocation
                    * The goal is to ANTICIPATE good allocations while PAST good allocations are missed oportunities
                """)
                st.plotly_chart(fig1, use_container_width=True)
                st.plotly_chart(fig2, use_container_width=True)
                st.plotly_chart(fig3, use_container_width=True)
            
        with sirius:
            if on_allocator and succcess_main_page:
                st.write("""
                    Sirius probablity is the score that gives you whether the asset price is going to go up or down
                    I deally we look for a score to go up higher than the go down

                         * Arrow down -> probability to go down
                         * Arrow up -> probability to go up
                """)
                fig = sirius_summary_plot(sirius_df,asset2color)
                st.plotly_chart(fig, use_container_width=True)
                fig3 =sirius_in_allocator_plot(sirius_df, map_targets, asset2color)
                st.plotly_chart(fig3, use_container_width=True)


