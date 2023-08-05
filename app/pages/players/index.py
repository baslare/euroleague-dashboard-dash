import dash
import numpy as np
from dash import Dash, html, dcc, dash_table, callback, Output, Input, State
import plotly.express as px
import pandas as pd
import requests
import igviz as ig
import networkx as nx
import plotly.graph_objects as go

dash.register_page(__name__, path="/players")


def layout():
    init_player = requests.get(f"http://euroleague-api:8989/InitPlayer")
    init_player = init_player.json()
    init_player = pd.DataFrame.from_dict(init_player)

    options = {y: x for x, y in zip(init_player["playerName"], init_player["PLAYER_ID"])}

    layout_local = html.Div(children=[
        html.Div([html.Div(dcc.Dropdown(
            options=options,
            value=[],
            id="dropdown-player-index"

        ),
            style={"width": "50%"}),
            html.Button('Submit', id='submit-val-player-index', n_clicks=0)], style={"display": "flex",
                                                                        "flex-direction": "row",
                                                                        "width": "50%"}),
        dcc.Location(id="location-player-index")
    ])
    return layout_local


@callback(
    Output("location-player-index", "pathname"),
    State(component_id="dropdown-player-index", component_property="value"),
    Input(component_id="submit-val-player-index", component_property="n_clicks"),
    prevent_initial_call=True
)
def navigate_to_url(val, n_clicks):
    return f"/players/{val}"