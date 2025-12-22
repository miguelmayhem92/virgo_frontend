from io import BytesIO
import datetime
from dateutil.relativedelta import relativedelta
from PIL import Image
import yaml
import time

from pathlib import Path
import seaborn as sns
import streamlit as st
import matplotlib.pyplot as plt
from utils import logo, execute_state_machine_allocator, dowload_any_object
from auth_utils_cognito import menu_with_redirect

from virgo_modules.src.ticketer_source import stock_eda_panel
from tooling.portfolio_utils import return_matrix, filter_scale_ts
from tooling.portfolio_utils import plot_individual_allocations, benchmark_allocations, sirius_in_allocator_plot

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
tickers = [x.strip() for x in tickers]
if st.button("add"):
    st.write(",".join(tickers))

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
            stock_code = tickers[0]
            object_stock = stock_eda_panel(stock_code , 1000, '5y')
            object_stock.get_data()
            object_stock.df = object_stock.df[["Date","Close"]].rename(columns={"Close": stock_code})
            for code in tickers[1:]:
                try:
                    object_stock.extract_sec_data(code, ["Date","Close"], {"Close":code})
                except:
                    st.error(f"{code} not found")

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
                        execution_time = datetime.strptime(execution_time_str, '%Y-%m-%d:%H:%M:%S')
                        current_execution_time = datetime.datetime.now()
                        elapsed_time = current_execution_time - execution_time
                        hours_elapsed = divmod(elapsed_time.total_seconds(), 60*60)[0]
                        return hours_elapsed
                    except:
                        hours_elapsed=24
                        return hours_elapsed
                
                hours_elapsed = get_execution_time()
                if hours_elapsed > EXECUTE_AFTER:
                    execute_state_machine_allocator({"asset_list":tickers})
                for i in range(15):
                    hours_elapsed = get_execution_time()
                    if hours_elapsed < EXECUTE_AFTER:
                        time.sleep(15)
                        print(f"waiting stepmachine to finish {i}")
                        continue
                    else:
                        print("done! step machine finished")
                        allocator_df = dowload_any_object(allocator_name, f'edge_models/andromeda/consolidate/', 'csv', bucket)
                        sirius_df = dowload_any_object(sirius_name, f'edge_models/andromeda/consolidate/', 'csv', bucket)
                        break
                # producing dashboards!!!
                fig1 = plot_individual_allocations(allocator_df, tickers)
                fig2 = benchmark_allocations(allocator_df, targets)
                st.plotly_chart(fig1, use_container_width=True)
                st.plotly_chart(fig2, use_container_width=True)
            
        with sirius:
            if on_allocator and succcess_main_page:
                fig3 =sirius_in_allocator_plot(sirius_df, map_targets)
                st.plotly_chart(fig3, use_container_width=True)

