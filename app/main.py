import os
from dash import Dash, html, dcc, dash_table, callback, Output, Input, State
import plotly.express as px
import pandas as pd
import requests

app = Dash(__name__)

server = app.server

app.layout = html.Div(
    children=[

        html.Div(["Enter game code",
                  dcc.Input(id="game-code-input", type="number", value=1)]),
        html.Button("Submit", id="submit-button", n_clicks=0),

        html.Div(dash_table.DataTable(id="teams-data-table", data=[])),
        html.Div(dcc.Graph(id="plot-bar", figure={})),
        dcc.Store(id="json-store")
    ]

)


@callback(
    Output(component_id="json-store", component_property="data"),
    Input(component_id="submit-button", component_property="n_clicks"),
    State(component_id="game-code-input", component_property="value")
)
def call_players_api(n_clicks, game_code):
    response = requests.get(f"http://euroleague-api:8989/GamePlayers?game_code={game_code}")
    response = response.json()
    return response


@callback(
    Output(component_id="plot-bar", component_property="figure"),
    Input(component_id="json-store", component_property="data")
)
def plot_game_points(response):
    df = pd.DataFrame.from_dict(response)
    df = df.groupby("CODETEAM").agg({"pts": "sum"}).reset_index()

    return px.bar(df, x="CODETEAM", y="pts")


@callback(
    Output(component_id="teams-data-table", component_property="data"),
    # Output(component_id="teams-data-table", component_property="columns"),
    Input(component_id="json-store", component_property="data")
)
def update_players_table(data):
    # df = pd.DataFrame.from_dict(data)
    # col_dict = [{"name": x, "id": x} for x in df.columns]

    return data


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050)
