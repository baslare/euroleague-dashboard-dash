import json
import dash_bootstrap_components as dbc
import dash
from dash import Dash, html, dcc, dash_table, callback, Output, Input, State
from dash.exceptions import PreventUpdate
import plotly.express as px
import pandas as pd
import requests

dash.register_page(__name__, path_template="/players/<player_id>")


def layout(player_id="PTGB"):
    id_store = dcc.Store(id="player-id-store", data=player_id)
    json_store_player = dcc.Store(id="json-store-player", data=[])

    layout_local = html.Div(

        children=[
            json_store_player,
            id_store,
            html.Div(id="player-table", children=[])
        ]

    )

    return layout_local


@callback(
    Output(component_id="json-store-player", component_property="data"),
    Input(component_id="player-id-store", component_property="data")
)
def call_players_api(player_id):
    response = requests.get(f"http://euroleague-api:8989/Player?player_id={player_id}")
    response = response.json()
    return response


@callback(
    Output(component_id="player-table", component_property="children"),
    Input(component_id="json-store-player", component_property="data"),
    Input(component_id="player-id-store", component_property="data")
)
def update_player_table(response, player_id):
    df = pd.DataFrame(response, index=[0])
    data = df.to_dict("records")

    cols = [{"name": i, "id": i} for i in df.columns]
    child = dash_table.DataTable(
        id='player-table-data',
        data=data,
        columns=cols)

    img_url = f"photos/{player_id}.png"

    return [html.Img(src=dash.get_asset_url(img_url)), child]
