import dash
import numpy as np
from dash import Dash, html, dcc, dash_table, callback, Output, Input, State
import plotly.express as px
import pandas as pd
import requests
import igviz as ig
import networkx as nx
import plotly.graph_objects as go

dash.register_page(__name__, path="/game")


def layout():
    layout_local = html.Div(
        children=[
            html.Div(["Enter game code",
                      dcc.Input(id="game-code-input-index", type="number", value=1),
                      html.Button('Submit', id='submit-val-game-index', n_clicks=0)], style={
                "display": "flex",
                "flex-direction": "row",
                "justify-content": "center",
                "width": "50%",
                "margin-top": "1rem"})
            ,
            dcc.Location(id="location-game-index")])

    return layout_local


@callback(
    Output("location-game-index", "pathname"),
    State(component_id="game-code-input-index", component_property="value"),
    Input(component_id="submit-val-game-index", component_property="n_clicks"),
    prevent_initial_call=True

)
def navigate_to_game_url(val, n_clicks):
    return f"/game/{val}"
