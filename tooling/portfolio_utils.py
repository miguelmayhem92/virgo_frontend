import gc

import numpy as np
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

def plot_individual_allocations(data,stock_codes, window=300):
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True,
                    subplot_titles=["Prices", "estimations","observed"],vertical_spacing=0.08)
    n_colors= len(COLOR_LIST)
    for i,asset in enumerate(stock_codes):
        i = i%n_colors
        color = COLOR_LIST[i]
        df = data[data["asset"]==asset].sort_values("Date").iloc[-window:]
        init = df["Close"].iloc[0]
        fig.add_trace(go.Scatter(x=df["Date"],y=df["Close"]/init,name=asset, showlegend=True,legendgroup=asset,line_color=color), row=1, col=1)
        feature = f"hat_optimal_asset_future_return"
        fig.add_trace(go.Scatter(x=df["Date"],y=df[feature],name=asset,legendgroup=asset,line_color=color, showlegend=False), row=2, col=1)
        feature = f"optimal_asset_future_return"
        fig.add_trace(go.Scatter(x=df["Date"],y=df[feature],name=asset,legendgroup=asset,line_color=color, showlegend=False), row=3, col=1)
    
    fig.update_layout(height=+900, width=1200, title_text="Individual candidate allocations")
    return fig

def quantile(q=0.5, **kwargs):
    def f(series):
        return series.quantile(q, **kwargs)
    return f
    
def benchmark_allocations(data,target_variables, window=300):
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True,subplot_titles=["Prices", "estimations","observed"])
    n_colors= len(COLOR_LIST)
    
    # closes
    for i,feature in enumerate(target_variables[1:]):
        i = i%n_colors
        color = COLOR_LIST[i]
        tag = feature.split("_")[1]
        aggr = data.groupby(["Date"],as_index=False).agg(
            Close = (tag,"max"),
        )
        aggr = aggr.sort_values("Date").iloc[-window:]
        init = aggr["Close"].iloc[0]
        ntag = bench_map[tag]
        fig.add_trace(go.Scatter(x=aggr["Date"],y=aggr["Close"]/init,name=ntag,legendgroup=ntag, showlegend=True,line_color=color), row=1, col=1)
        
    # predicted
    for i,feature in enumerate(target_variables[1:]):
        i = i%n_colors
        color = COLOR_LIST[i]
        feature = f"hat_{feature}"
        tag = feature.split("_")[2]
        tag = bench_map[tag]
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
        fig.add_trace(go.Scatter(x=aggr["Date"],y=aggr[f"q25_{feature}"],name=tag,legendgroup=tag, showlegend=False,line_color=color), row=2, col=1)
        fig.add_trace(go.Scatter(x=aggr["Date"],y=aggr[f"q50_{feature}"],name=tag,legendgroup=tag, showlegend=False,line_color=color), row=2, col=1)
        fig.add_trace(go.Scatter(x=aggr["Date"],y=aggr[f"q75_{feature}"],name=tag,legendgroup=tag, showlegend=False,line_color=color), row=2, col=1)
    
    # actual
    for i,feature in enumerate(target_variables[1:]):
        i = i%n_colors
        color = COLOR_LIST[i]
        tag = feature.split("_")[1]
        tag = bench_map[tag]
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
        fig.add_trace(go.Scatter(x=aggr["Date"],y=aggr[f"q25_{feature}"],name=tag,legendgroup=tag, showlegend=False,line_color=color), row=3, col=1)
        fig.add_trace(go.Scatter(x=aggr["Date"],y=aggr[f"q50_{feature}"],name=tag,legendgroup=tag, showlegend=False,line_color=color), row=3, col=1)
        fig.add_trace(go.Scatter(x=aggr["Date"],y=aggr[f"q75_{feature}"],name=tag,legendgroup=tag, showlegend=False,line_color=color), row=3, col=1)
        
    fig.update_layout(height=900, width=1200, title_text="benchmarks candidate allocations")
    return fig

def sirius_in_allocator_plot(data_plot,map_targets, data_window=550, window=4):
    n_colors= len(COLOR_LIST)
    fig = make_subplots(
        rows=len(map_targets.keys()), cols=1, shared_xaxes=True,subplot_titles=[f"smooth {v}" for k,v in map_targets.items()],
            vertical_spacing=0.08)
    for j,asset_name in enumerate(data_plot.asset.unique()):
        j = j%n_colors
        color = COLOR_LIST[j]
        df = data_plot[data_plot.asset == asset_name].iloc[-data_window:].copy()
        for rowi,target in enumerate(map_targets.keys()):
            legend = True if rowi == 0 else False 
            df[f"smooth_{target}"] = df.sort_values("Date")[target].rolling(window,min_periods=1).mean()
            fig.add_trace(go.Scatter(x=df["Date"],y=df[f"smooth_{target}"],name=asset_name,legendgroup=asset_name, showlegend=legend,line_color=color), row=rowi+1, col=1)
        del df
        gc.collect()
    fig.update_layout(height=800, width=1200, title_text="sirius smoothed probabilities")
    return fig