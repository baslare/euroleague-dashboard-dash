import json
import dash_bootstrap_components as dbc
import dash
from dash import Dash, html, dcc, dash_table, callback, Output, Input, State
from dash.exceptions import PreventUpdate
import plotly.express as px
import pandas as pd
import requests

dash.register_page(__name__, location="none")


def layout(player_id="PTGB"):
    id_store = dcc.Store(id="player-id-store", data=player_id)
    json_store = dcc.Store(id="player-id-json", data=call_players_api(0, player_id))

    layout_local = html.Div(
        children=[
            html.Div(children=f"Player ID: {id_store.data}", id="player-stat-as"),
            html.Div(children=f"Assists: {json_store.data['AS']}", id="player-stat-as"),


        ] + [html.Div(children=f"{x}: {json_store.data.get(x)}", id=f"player-stat-{x}") for x in json_store.data.keys()]

    )

    return layout_local


@callback(
    Output(component_id="player-id-json", component_property="data"),
    Input(component_id="submit-button-player", component_property="n_clicks"),
    State(component_id="player-id-input", component_property="value")
)
def call_players_api(n_clicks, player_id):
    response = requests.get(f"http://euroleague-api:8989/Player?player_id={player_id}")
    response = response.json()
    return response


@callback(
    Output(component_id="player-data-table", component_property="data"),
    # Output(component_id="teams-data-table", component_property="columns"),
    Input(component_id="player-id-json", component_property="data")
)
def update_player_table(data):
    df = pd.Series(data).to_frame().transpose().apply(lambda x: list(x))
    # col_dict = [{"name": x, "id": x} for x in df.columns]
    return json.dumps(df.to_json("records"))


@callback(
    Output(component_id="player-stat-as", component_property="children"),
    Input(component_id="player-id-json", component_property="data")
)
def print_stats(data):
    return data["AS"]
