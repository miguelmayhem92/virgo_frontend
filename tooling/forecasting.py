from plotly.subplots import make_subplots
import plotly.graph_objects as go

def plot_forecastings(asset:str, data_caontainer:dict, n_obs=50):
    result_df= data_caontainer["result_df"]
    average_1step_forecast= data_caontainer["average_1step_forecast"]
    average_25_1step_forecast= data_caontainer["average_25_1step_forecast"]
    average_75_1step_forecast= data_caontainer["average_75_1step_forecast"]
    conformal_25_result_df= data_caontainer["conformal_25_result_df"]
    conformal_75_result_df= data_caontainer["conformal_75_result_df"]
    
    
    df=result_df[result_df["asset"]==asset].sort_values("Date").tail(n_obs)
    df_past = average_1step_forecast[average_1step_forecast["asset"]==asset].sort_values("Date").tail(n_obs)
    df_25 = average_25_1step_forecast[average_25_1step_forecast["asset"]==asset].sort_values("Date").tail(n_obs)
    df_75 = average_75_1step_forecast[average_75_1step_forecast["asset"]==asset].sort_values("Date").tail(n_obs)
    dff_75 = conformal_75_result_df[conformal_75_result_df["asset"]==asset].sort_values("Date").tail(n_obs)
    dff_25 = conformal_25_result_df[conformal_25_result_df["asset"]==asset].sort_values("Date").tail(n_obs)

    lags = 4
    fig = make_subplots(
                rows= 1, cols=2,vertical_spacing = 0.05, horizontal_spacing = 0.05,
                specs=[
                    [{"type": "scatter"}, {"type": "scatter"}]],
                subplot_titles = [f'asset returns {lags} lags', 'closing prices', 'hidden states']
        )
    

    fig.add_trace(go.Scatter(x=df[df["type"]=="observed"]["Date"],y=df[df["type"]=="observed"]["log_return"], marker_color="blue",showlegend=False),row=1, col=1)
    fig.add_trace(go.Scatter(x=df[df["type"]=="forecast"]["Date"], y=df[df["type"]=="forecast"]["log_return"], marker_color="red", opacity =0.5,showlegend=False),row=1, col=1)
    fig.add_trace(go.Scatter(x=dff_75[dff_75["type"]=="forecast"]["Date"], y=dff_75[dff_75["type"]=="forecast"]["log_return"], marker_color="green", opacity =0.5,showlegend=False),row=1, col=1)
    fig.add_trace(go.Scatter(x=dff_25[dff_25["type"]=="forecast"]["Date"], y=dff_25[dff_25["type"]=="forecast"]["log_return"], marker_color="green", opacity =0.5,showlegend=False),row=1, col=1)
    fig.add_trace(go.Scatter(x=df_past[df_past["type"]=="observed"]["Date"], y=df_past[df_past["type"]=="observed"]["pred_1"], marker_color="grey", opacity =0.5,showlegend=False),row=1, col=1)
    fig.add_trace(go.Scatter(x=df_25[df_25["type"]=="observed"]["Date"], y=df_25[df_25["type"]=="observed"]["conf_lower_target_1"], marker_color="grey", opacity =0.5,showlegend=False),row=1, col=1)
    fig.add_trace(go.Scatter(x=df_75[df_75["type"]=="observed"]["Date"], y=df_75[df_75["type"]=="observed"]["conf_upper_target_1"], marker_color="grey", opacity =0.5,showlegend=False),row=1, col=1)
    fig.add_hline(y=0, line_width=2, line_dash="dash", line_color="grey",col = 1, row = 1)


    fig.add_trace(go.Scatter(x=df[df["type"]=="observed"]["Date"], y=df[df["type"]=="observed"]["Close"], marker_color="blue",showlegend=False),row=1, col=2)
    fig.add_trace(go.Scatter(x=df[df["type"]=="forecast"]["Date"], y=df[df["type"]=="forecast"]["Close"], marker_color="red", opacity =0.5,showlegend=False),row=1, col=2)
    fig.add_trace(go.Scatter(x=dff_75[dff_75["type"]=="forecast"]["Date"], y=dff_75[dff_75["type"]=="forecast"]["Close"], marker_color="green", opacity =0.5,showlegend=False),row=1, col=2)
    fig.add_trace(go.Scatter(x=dff_25[dff_25["type"]=="forecast"]["Date"], y=dff_25[dff_25["type"]=="forecast"]["Close"], marker_color="green", opacity =0.5,showlegend=False),row=1, col=2)
    fig.add_trace(go.Scatter(x=df_past[df_past["type"]=="observed"]["Date"], y=df_past[df_past["type"]=="observed"]["forecast_1"], marker_color="grey", opacity =0.5,showlegend=False),row=1, col=2)
    fig.add_trace(go.Scatter(x=df_25[df_25["type"]=="observed"]["Date"], y=df_25[df_25["type"]=="observed"]["forecast_1"], marker_color="grey", opacity =0.5,showlegend=False),row=1, col=2)
    fig.add_trace(go.Scatter(x=df_75[df_75["type"]=="observed"]["Date"], y=df_75[df_75["type"]=="observed"]["forecast_1"], marker_color="grey", opacity =0.5,showlegend=False),row=1, col=2)

    return fig