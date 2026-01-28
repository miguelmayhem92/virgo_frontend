import gc
import datetime
from dateutil.relativedelta import relativedelta

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly
from plotly.subplots import make_subplots

COLOR_LIST = [
    '#1f77b4',  # muted blue
    '#ff7f0e',  # safety orange
    '#2ca02c',  # cooked asparagus green
    '#d62728',  # brick red
    '#9467bd',  # muted purple
    '#8c564b',  # chestnut brown
    '#e377c2',  # raspberry yogurt pink
    '#7f7f7f',  # middle gray
    '#bcbd22',  # curry yellow-green
    '#17becf'   # blue-teal
]

bench_map = {
    "bench1":"sp500",
    "bench2":"dax",
    "bench3":"nikkei",
    "bench4":"gold",
    "bench5":"copper"
}

def return_matrix(data, features, lags, apply_log=False):
    data = data.sort_values("Date").copy()
    if apply_log:
        for code in features:
            data[code] = np.log(data[code]/data[code].shift(lags))
    else:
        for code in features:
            data[code] = data[code]/data[code].shift(lags)-1
    return data.dropna()

def filter_scale_ts(data, date, features,trad_days = 7,lags=3):
    df = data[data["Date"] >= date].sort_values("Date").set_index("Date").copy()
    df_1 = df.iloc[0]
    df = df/df_1

    fig = make_subplots(rows=2, cols=1,shared_xaxes=True,vertical_spacing=0.02)
    colors = plotly.colors.DEFAULT_PLOTLY_COLORS
    for i,code in enumerate(features):
        color=colors[i%len(colors)]
        fig.add_trace(go.Scatter(x=df.index, y=df[code],
                    mode='lines+markers',
                    legendgroup=code,
                    line = dict(color=color),
                    name=code),col=1,row=1)
    data=data[data["Date"] >= date].sort_values("Date").set_index("Date").copy()
    for code in features:
        data[code] = np.log(data[code]/data[code].shift(lags))
        data[code] = np.square(data[code])
        data[code] = data[code].rolling(window = trad_days).std()*np.sqrt(252)
    for i,code in enumerate(features):
        color=colors[i%len(colors)]
        fig.add_trace(go.Scatter(x=data.index, y=data[code],
                    mode='lines+markers',
                    legendgroup=code,
                    showlegend=False,
                    line = dict(color=color),
                    name=code),col=1,row=2)
    fig.update_layout(height=700,width=1000,title="Time series view of multiple assets")
    return fig

def quantile(q=0.5, **kwargs):
    def f(series):
        return series.quantile(q, **kwargs)
    return f
    
def asset_to_color(stock_codes, target_variable):
    full_asset_list = stock_codes + [bench_map[tag.split("_")[1]] for tag in target_variable[1:]]
    asset2color = {x:COLOR_LIST[i%len(COLOR_LIST)] for i,x in enumerate(full_asset_list)}
    return asset2color

def sirius_in_allocator_plot(data_plot,map_targets, asset2color, data_window=550, window=4):
    fig = make_subplots(
        rows=len(map_targets.keys()), cols=1, shared_xaxes=True,subplot_titles=[f"smooth {v}" for k,v in map_targets.items()],
            vertical_spacing=0.08)
    for j,asset_name in enumerate(data_plot.asset.unique()):
        color = asset2color.get(asset_name)
        df = data_plot[data_plot.asset == asset_name].iloc[-data_window:].copy()
        for rowi,target in enumerate(map_targets.keys()):
            legend = True if rowi == 0 else False 
            df[f"smooth_{target}"] = df.sort_values("Date")[target].rolling(window,min_periods=1).mean()
            fig.add_trace(go.Scatter(x=df["Date"],y=df[f"smooth_{target}"],name=asset_name,legendgroup=asset_name, showlegend=legend,line_color=color), row=rowi+1, col=1)
        del df
        gc.collect()
    fig.update_layout(height=800, width=1200, title_text="sirius smoothed probabilities")
    return fig


def plot_ts_allocations(data,stock_codes, target_variables, asset2color, window=100):
    fig = make_subplots(rows=3, cols=2, shared_xaxes=True,
                    subplot_titles=["Prices","Prices", "estimations","estimations","observed","observed"],vertical_spacing=0.08)
    new_color_list = list()
    ## individual allocations
    for asset in stock_codes:
        try:
            color = asset2color.get(asset)
            df = data[data["asset"]==asset].sort_values("Date").iloc[-window:]
            init = df["Close"].iloc[0]
            fig.add_trace(go.Scatter(x=df["Date"],y=df["Close"]/init,name=asset, showlegend=True,legendgroup=asset,line_color=color), row=1, col=1)
            feature = f"hat_optimal_asset_future_return"
            fig.add_trace(go.Scatter(x=df["Date"],y=df[feature],name=asset,legendgroup=asset,line_color=color, showlegend=False), row=2, col=1)
            feature = f"optimal_asset_future_return"
            fig.add_trace(go.Scatter(x=df["Date"],y=df[feature],name=asset,legendgroup=asset,line_color=color, showlegend=False), row=3, col=1)
            new_color_list.append(color)
        except:
            continue

    ## benchmark allocations
    # closes
    for feature in target_variables[1:]:
        tag = feature.split("_")[1]
        aggr = data.groupby(["Date"],as_index=False).agg(
            Close = (tag,"max"),
        )
        aggr = aggr.sort_values("Date").iloc[-window:]
        init = aggr["Close"].iloc[0]
        ntag = bench_map[tag]
        color = asset2color.get(ntag)
        fig.add_trace(go.Scatter(x=aggr["Date"],y=aggr["Close"]/init,name=ntag,legendgroup=ntag, showlegend=True,line_color=color), row=1, col=2)
        
    # predicted
    for feature in target_variables[1:]:
        feature = f"hat_{feature}"
        tag = feature.split("_")[2]
        tag = bench_map[tag]
        color = asset2color.get(tag)
        aggr = data.groupby(["Date"],as_index=False).agg(
            q25 = (feature, quantile(0.25)),
            q50 = (feature, quantile(0.50)),
            q75 = (feature, quantile(0.75)),
        ).rename(columns={
            "q25":f"q25_{feature}",
            "q50":f"q50_{feature}",
            "q75":f"q75_{feature}",
        })
        aggr = aggr.sort_values("Date").iloc[-window:]
        fig.add_trace(go.Scatter(x=aggr["Date"],y=aggr[f"q25_{feature}"],name=tag,legendgroup=tag, showlegend=False,line_color=color), row=2, col=2)
        fig.add_trace(go.Scatter(x=aggr["Date"],y=aggr[f"q50_{feature}"],name=tag,legendgroup=tag, showlegend=False,line_color=color), row=2, col=2)
        fig.add_trace(go.Scatter(x=aggr["Date"],y=aggr[f"q75_{feature}"],name=tag,legendgroup=tag, showlegend=False,line_color=color), row=2, col=2)
    
    # actual
    for feature in target_variables[1:]:
        tag = feature.split("_")[1]
        tag = bench_map[tag]
        color = asset2color.get(tag)
        aggr = data.groupby(["Date"],as_index=False).agg(
            q25 = (feature, quantile(0.25)),
            q50 = (feature, quantile(0.50)),
            q75 = (feature, quantile(0.75)),
        ).rename(columns={
            "q25":f"q25_{feature}",
            "q50":f"q50_{feature}",
            "q75":f"q75_{feature}",
        })
        aggr = aggr.sort_values("Date").iloc[-window:]
        fig.add_trace(go.Scatter(x=aggr["Date"],y=aggr[f"q25_{feature}"],name=tag,legendgroup=tag, showlegend=False,line_color=color), row=3, col=2)
        fig.add_trace(go.Scatter(x=aggr["Date"],y=aggr[f"q50_{feature}"],name=tag,legendgroup=tag, showlegend=False,line_color=color), row=3, col=2)
        fig.add_trace(go.Scatter(x=aggr["Date"],y=aggr[f"q75_{feature}"],name=tag,legendgroup=tag, showlegend=False,line_color=color), row=3, col=2)
   
    fig.update_layout(height=+900, width=1200, title_text="allocations candidate and allocations")
    return fig

def pie_plots_candidates(data,stock_codes,asset2color, window_allocation=4):
    fig = make_subplots(rows=1, cols=2,
                        specs=[[{"type": "domain"}, {"type": "domain"}]],
                        subplot_titles=["estimated candidates", "past actual"],vertical_spacing=0.08)
    n_colors= len(COLOR_LIST)
    new_color_list = list()
    for i,asset in enumerate(stock_codes):
        try:
            color = asset2color.get(asset)
            df = data[data["asset"]==asset].sort_values("Date")
            new_color_list.append(color)
        except:
            continue
    max_date = data["Date"].max()
    begin_date = datetime.datetime.strptime(max_date , '%Y-%m-%d') - relativedelta(days=window_allocation)
    data_ = data[data["Date"] >= begin_date.strftime('%Y-%m-%d')]
    data_agr = data_.groupby(["asset"],as_index=False).agg(allocation=(f"hat_optimal_asset_future_return","mean"))
    data_agr["allocation"] = data_agr["allocation"]*100
    data_agr["allocation"] = data_agr["allocation"].round(2)
    data_agr['asset_cat'] = pd.Categorical(
        data_agr['asset'], 
        categories=stock_codes, 
        ordered=True
    )
    data_agr = data_agr.sort_values('asset_cat')
    fig.add_trace(go.Pie(labels=data_agr["asset"],values=data_agr["allocation"],
                         textinfo='label+value+percent',
                         showlegend=False,marker=dict(colors=new_color_list), hole=.3), row=1, col=1)
    
    max_date_ = datetime.datetime.strptime(max_date , '%Y-%m-%d') - relativedelta(days=10)
    begin_date = max_date_ - relativedelta(days=10)
    data_ = data[data["Date"] >= begin_date.strftime('%Y-%m-%d')]
    data_agr = data_.groupby(["asset"],as_index=False).agg(allocation=(f"optimal_asset_future_return","mean"))
    data_agr["allocation"] = data_agr["allocation"]*100
    data_agr["allocation"] = data_agr["allocation"].round(2)
    data_agr['asset_cat'] = pd.Categorical(
        data_agr['asset'], 
        categories=stock_codes, 
        ordered=True
    )
    data_agr = data_agr.sort_values('asset_cat')
    fig.add_trace(go.Pie(labels=data_agr["asset"],values=data_agr["allocation"],
                         textinfo='label+value+percent',
                         showlegend=False,marker=dict(colors=new_color_list), hole=.3), row=1, col=2)

    
    fig.update_layout(height=+500, width=1200, title_text="Individual candidate allocations")
    return fig

def pie_plots_benchmarks(data, target_variables,asset2color,window_allocation=4):
    fig = make_subplots(rows=1, cols=2, 
                        specs=[[{"type": "domain"}, {"type": "domain"}]],
                    subplot_titles=["estimated benchmark", "past actual"],vertical_spacing=0.08)
    n_colors= len(COLOR_LIST)
    new_color_list = list()
    list_pd = list()
    
    # predicted
    for feature in target_variables[1:]:
        feature = f"hat_{feature}"
        tag = feature.split("_")[2]
        tag = bench_map[tag]
        color = asset2color[tag]
        aggr = data.groupby(["Date"],as_index=False).agg(
            q50 = (feature, quantile(0.50)),
        ).rename(columns={
            "q50":f"q50_{feature}",
        })
        max_date = aggr["Date"].max()
        begin_date = datetime.datetime.strptime(max_date , '%Y-%m-%d') - relativedelta(days=window_allocation)
        aggr = aggr[aggr["Date"] >= begin_date.strftime('%Y-%m-%d')]
        aggr = aggr.sort_values("Date")
        aggr["asset"] = tag
        aggr = aggr.groupby("asset",as_index=False).agg(allocation=(f"q50_{feature}","mean"))
        new_color_list.append(color)
        list_pd.append(aggr.copy())
    aggr_df = pd.concat(list_pd)
    aggr_df["allocation"] = aggr_df["allocation"]*100
    aggr_df["allocation"] = aggr_df["allocation"].round(2)

    fig.add_trace(go.Pie(labels=aggr_df["asset"],values=aggr_df["allocation"],
                         textinfo='label+value+percent',
                         showlegend=False,marker=dict(colors=new_color_list), hole=.3), row=1, col=1)

    ## actual
    for feature in target_variables[1:]:
        tag = feature.split("_")[1]
        tag = bench_map[tag]
        color = asset2color[tag]
        aggr = data.groupby(["Date"],as_index=False).agg(
            q50 = (feature, quantile(0.50)),
        ).rename(columns={
            "q50":f"q50_{feature}",
        })
        max_date = aggr["Date"].max()
        max_date_ = datetime.datetime.strptime(max_date , '%Y-%m-%d') - relativedelta(days=10)
        begin_date = max_date_ - relativedelta(days=window_allocation)
        aggr = aggr[
            (aggr["Date"] >= begin_date.strftime('%Y-%m-%d'))
            &
            (aggr["Date"] < max_date_.strftime('%Y-%m-%d'))
        ]
        aggr = aggr.sort_values("Date")
        aggr["asset"] = tag
        aggr = aggr.groupby("asset",as_index=False).agg(allocation=(f"q50_{feature}","mean"))
        new_color_list.append(color)
        list_pd.append(aggr.copy())
    aggr_df = pd.concat(list_pd)
    aggr_df["allocation"] = aggr_df["allocation"]*100
    aggr_df["allocation"] = aggr_df["allocation"].round(2)

    fig.add_trace(go.Pie(labels=aggr_df["asset"],values=aggr_df["allocation"],
                         textinfo='label+value+percent',
                         showlegend=False,marker=dict(colors=new_color_list), hole=.3), row=1, col=2)
   
    fig.update_layout(height=+500, width=1200, title_text="allocations candidate and allocations")
    return fig

def sirius_summary_plot(data, asset2color,window=4):
    data[f'mean_proba_target_down'] = data.groupby(['asset'])["proba_target_down"].rolling(window,min_periods=2).mean().reset_index(level=0, drop=True)
    data[f'mean_proba_target_up'] = data.groupby(['asset'])["proba_target_up"].rolling(window,min_periods=2).mean().reset_index(level=0, drop=True)
    data['rn'] = data.sort_values("Date",ascending=False).groupby(['asset']).cumcount()+1
    data["diff"] =  data[f'mean_proba_target_down'] - data[f'mean_proba_target_up']
    result = data[(data["rn"] == 1)].sort_values("diff",ascending=False)

    fig = make_subplots(rows=1, cols=1)
    for asset in result.asset.unique():
        color = asset2color.get(asset)
        df = result[result.asset == asset]
        fig.add_trace(go.Scatter(x=df["asset"],y=df[f"mean_proba_target_down"],marker_size=15,hovertemplate="prob go up: %{y}",
                                 name=asset,legendgroup=asset,line_color=color,marker_symbol="triangle-up"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df["asset"],y=df[f"mean_proba_target_up"],marker_size=15,hovertemplate="prob go down: %{y}",
                                 name=asset,legendgroup=asset,showlegend=False,marker_symbol="triangle-down",line_color=color), row=1, col=1)
    fig.update_layout(height=400, width=1200, title_text="sirius probas summary")
    return fig