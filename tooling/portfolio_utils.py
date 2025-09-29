import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly
from plotly.subplots import make_subplots

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