import dash
import dash_bootstrap_components as dbc
from dash import Dash, html, dcc, dash_table, callback, Output, Input, State
from dash.exceptions import PreventUpdate
import plotly.express as px
import pandas as pd
import requests

dash.register_page(__name__,  location="none")


layout = html.Div(
    children=[
        html.Div(["Enter game code",
                  dcc.Input(id="game-code-input-lineup", type="number", value=1)]),
        html.Button("Submit", id="submit-button-lineup", n_clicks=0),

        html.Div(dash_table.DataTable(id="lineups-data-table", data=[])),
        dcc.Store(id="json-store-lineup")
    ]

)


@callback(
    Output(component_id="json-store-lineup", component_property="data"),
    Input(component_id="submit-button-lineup", component_property="n_clicks"),
    State(component_id="game-code-input-lineup", component_property="value")
)
def call_game_lineups_api(n_clicks, game_code):
    if game_code < 1:
        raise PreventUpdate
    response = requests.get(f"http://euroleague-api:8989/LineupSingleGameStats?game_code={game_code}")
    response = response.json()
    return response


@callback(
    Output(component_id="lineups-data-table", component_property="data"),
    # Output(component_id="teams-data-table", component_property="columns"),
    Input(component_id="json-store-lineup", component_property="data")
)
def update_lineup_table(data):
    # df = pd.DataFrame.from_dict(data)
    # col_dict = [{"name": x, "id": x} for x in df.columns]

    return data