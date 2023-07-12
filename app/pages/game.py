import json

import dash
import dash_bootstrap_components as dbc
from dash import Dash, html, dcc, dash_table, callback, Output, Input, State
from dash.dcc import Store
from dash.exceptions import PreventUpdate
import plotly.express as px
import pandas as pd
import requests

dash.register_page(__name__)

json_store = dcc.Store(id="json-store", data={})
json_store_team = dcc.Store(id="json-store-teams", data={})
json_store_points = dcc.Store(id="json-store-points", data={})
key_stats_json = dcc.Store(id="key-stats-json", data=[])

layout = html.Div(
    children=[
        json_store,
        json_store_team,
        json_store_points,
        key_stats_json,
        html.Div(["Enter game code",
                  dcc.Input(id="game-code-input", type="number", value=1)]),
        html.Div(id="score-title", style={"height": "100px",
                                          "width": "700px",
                                          "display": "flex",
                                          "align-items": "center",
                                          "justify-content": "center",
                                          "position": "relative",
                                          "left": "50%",
                                          "transform": "translate(-50%,0)"}),
        html.Div(id="key-stats", children=[], style={
            "display": "flex",
            "align-items": "center",
            "justify-content": "center"}),
        html.Div(dcc.Graph(figure=[], id="points-home")),

    ],
    style={"display": "flex",
           "flex-direction": "column",
           "justify-content": "center",
           }

)


@callback(
    Output(component_id="json-store", component_property="data"),
    Input(component_id="game-code-input", component_property="value")
)
def call_players_api(game_code):
    response = requests.get(f"http://euroleague-api:8989/GamePlayers?game_code={game_code}")
    response = response.json()
    return response


@callback(
    Output(component_id="score-title", component_property="children"),
    Input(component_id="json-store", component_property="data")
)
def plot_game_points(response):
    df = pd.DataFrame.from_dict(response)
    df = df.groupby(["CODETEAM", "home"]).agg({"pts": "sum"}).reset_index()
    home_score = df.loc[df["home"], "pts"].iloc[0]
    away_score = df.loc[~df["home"], "pts"].iloc[0]

    home_team = df.loc[df["home"], "CODETEAM"].iloc[0]
    away_team = df.loc[~df["home"], "CODETEAM"].iloc[0]

    home_img_url = f"{home_team}.png"
    away_img_url = f"{away_team}.png"

    return [html.Img(src=dash.get_asset_url(home_img_url), style={"height": "100%"}),
            html.H2(f"{home_team} {home_score} - {away_score} {away_team}",
                    style={"textAlign": "center", "width": "50%"}),
            html.Img(src=dash.get_asset_url(away_img_url), style={"height": "100%"})]


@callback(
    Output(component_id="teams-data-table", component_property="data"),
    # Output(component_id="teams-data-table", component_property="columns"),
    Input(component_id="json-store", component_property="data")
)
def update_players_table(response):
    # df = pd.DataFrame.from_dict(data)
    # col_dict = [{"name": x, "id": x} for x in df.columns]

    return response


@callback(
    Output(component_id="json-store-teams", component_property="data"),
    Input(component_id="game-code-input", component_property="value")
)
def call_game_lite_api(game_code):
    response = requests.get(f"http://euroleague-api:8989/GameLite?game_code={game_code}")
    response = response.json()
    return response


@callback(
    Output(component_id="key-stats-json", component_property="data"),
    Input(component_id="json-store-teams", component_property="data")
)
def update_key_stats_df(response):
    df = pd.DataFrame.from_dict(response)

    mid_col = ["2P%", "3P%", "FT%", "DREB%", "OREB%", "AS", "TO", "ST", "BL", "POS", "ORtg"]

    l_u_1 = f"{df.loc[df['home'], '2FGM'].iloc[0]} / {df.loc[df['home'], '2FGA'].iloc[0]} ({100 * df.loc[df['home'], '2FGR'].iloc[0]:.2f}%)"
    l_u_2 = f"{df.loc[df['home'], '3FGM'].iloc[0]} / {df.loc[df['home'], '3FGA'].iloc[0]} ({100 * df.loc[df['home'], '3FGR'].iloc[0]:.2f}%)"
    l_u_3 = f"{df.loc[df['home'], 'FTM'].iloc[0]} / {df.loc[df['home'], 'FTA'].iloc[0]} ({100 * df.loc[df['home'], 'FTR'].iloc[0]:.2f}%)"
    l_u_4 = f"{df.loc[df['home'], 'D'].iloc[0]}  ({100 * df.loc[df['home'], 'DRBEBR'].iloc[0]:.2f}%)"
    l_u_5 = f"{df.loc[df['home'], 'O'].iloc[0]}  ({100 * df.loc[df['home'], 'ORBEBR'].iloc[0]:.2f}%)"
    l_rest = [f"{df.loc[df['home'], x].iloc[0]}" for x in ["AS", "TO", "ST", "FV", "pos"]]
    l_l_1 = f"{100 * df.loc[df['home'], 'PPP'].iloc[0]:.2f}"

    r_u_1 = f"{df.loc[~df['home'], '2FGM'].iloc[0]} / {df.loc[~df['home'], '2FGA'].iloc[0]} ({100 * df.loc[~df['home'], '2FGR'].iloc[0]:.2f}%)"
    r_u_2 = f"{df.loc[~df['home'], '3FGM'].iloc[0]} / {df.loc[~df['home'], '3FGA'].iloc[0]} ({100 * df.loc[~df['home'], '3FGR'].iloc[0]:.2f}%)"
    r_u_3 = f"{df.loc[~df['home'], 'FTM'].iloc[0]} / {df.loc[~df['home'], 'FTA'].iloc[0]} ({100 * df.loc[~df['home'], 'FTR'].iloc[0]:.2f}%)"
    r_u_4 = f"{df.loc[~df['home'], 'D'].iloc[0]}  ({100 * df.loc[~df['home'], 'DRBEBR'].iloc[0]:.2f}%)"
    r_u_5 = f"{df.loc[~df['home'], 'O'].iloc[0]}  ({100 * df.loc[~df['home'], 'ORBEBR'].iloc[0]:.2f}%)"
    r_rest = [f"{df.loc[~df['home'], x].iloc[0]}" for x in ["AS", "TO", "ST", "FV", "pos"]]
    r_l_1 = f"{100 * df.loc[~df['home'], 'PPP'].iloc[0]:.2f}"

    left_col = [l_u_1, l_u_2, l_u_3, l_u_4, l_u_5, *l_rest, l_l_1]
    right_col = [r_u_1, r_u_2, r_u_3, r_u_4, r_u_5, *r_rest, r_l_1]

    df_return = pd.DataFrame.from_dict({
        "left_col": left_col,
        "mid_col": mid_col,
        "right_col": right_col})

    return df_return.to_json(orient="split")


@callback(Output('key-stats', 'children'),
          [Input('key-stats-json', 'data')])
def update_key_stats_output(json_df):
    info_dataframe = pd.read_json(json_df, orient='split')

    data = info_dataframe.to_dict("records")
    cols = [{"name": i, "id": i} for i in info_dataframe.columns]

    child = [
        dash_table.DataTable(
            id='key-stats-table',
            data=data,
            columns=cols,
            style_as_list_view=True,
            style_data_conditional=[
                {"if": {"column_id": "left_col"},
                 "textAlign": "right"},
                {"if": {"column_id": "mid_col"},
                 "textAlign": "center",
                 "font-weight": "bold"},
                {"if": {"column_id": "right_col"},
                 "textAlign": "left"}

            ],
            style_header={"display": "none"},
            style_cell={"font_size": "12px"},
            fill_width=False

        )
    ]
    return child


@callback(
    Output(component_id="json-store-points", component_property="data"),
    Input(component_id="game-code-input", component_property="value")
)
def call_points_single_game_api(game_code):
    response = requests.get(f"http://euroleague-api:8989/PointsSingleGame?game_code={game_code}")
    response = response.json()
    return response


@callback(
    Output(component_id="points-home", component_property="figure"),
    Input(component_id="json-store-points", component_property="data")
)
def plot_points(response):
    df = pd.DataFrame.from_dict(response)

    return px.scatter(df, x="x_new", y="y_new", color="missed")
