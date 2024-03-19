# VIRGO FRONTEND

This repo has the code to run Streamlit in the Streamlit cloud community.

structure:

* built with:
* pages
* utils
* testing and running

-----------------------------

## repo structure

```
.
├── images
|   └── log_white.png
├── .streamlit
|   ├── config.toml
|   └── secrets.toml
├── pages
|   ├── asset_deep_dive.py
|   ├── asset_explore.py
|   ├── markets.py
|   └── multiple_symbols.py
├── README
├── .gitignore
├── configs.yaml
├── requirements.txt
├── secrets.toml
└── utils.py
```

## built with

Find the libraries in the requirements txt file. 
the dependencies are:
- Python 3.9.x
- streamlit, streamlit-extras, st-pages, s3fs, st-files-connection
- pyyaml
- matplotlib, plotly
- virgo-modules
- boto3
- pandas, pykalman

## Pages

##### Hello World

home page and main  page to run the app

##### pages/asset deep dive

Analysis of monitoring assets, here the repo: https://github.com/miguelmayhem92/virgo_asset_lambda

##### pages/asset explore

Global signal plots and edge ML model, here the repo: https://github.com/miguelmayhem92/virgo_edge_models_lambda

##### pages/markets

Index monitoring and forecasting model, here the repos: https://github.com/miguelmayhem92/virgo_marketindex_lambda and https://github.com/miguelmayhem92/virgo_api_market_forecast_lambda

##### pages/multiple symbols

Ranking and recomendations, Here the repo: https://github.com/miguelmayhem92/virgo_rankings_lambda

## Utils

the utils folder have code snippets:
- reading objects from s3
- call endpoints
- streamlit objects

## Testing and running

```
streamlit run hello_world.py
```