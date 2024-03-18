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

<b> Hello World

home page and main  page to run the app

<b> pages/asset deep dive

<b> pages/asset explore

<b> pages/markets

<b> pages/multiple symbols

## Utils


## Testing and running
