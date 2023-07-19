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

    highlight_stats = ["playerName","game_count","pts_avg", "2FGP",
                       "3FGR", "FTR", "AS_avg", "D_avg",
                       "O_avg", "TO_avg", "PIR_avg", "plus_minus_avg",
                       "DREBR","OREBR", "usage",
                       "on_ORtg_avg", "off_ORtg_avg"]

    stat_keys = ["AS", "TO", "3FGM", "3FGA", "2FGA", "2FGM",
                 "FTM", "FTA", "D", "O", "REB",
                 "RV", "CM", "FV", "AG", "ST", "OF", "CMT", "CMU", "CMD",
                 "multi_ft", "assisted_2fg", "assisted_3fg",
                 "assisted_ft", "and_one_2fg", "and_one_3fg", "pos"]

    df_self = df.loc[0, stat_keys].reset_index(drop=True)
    df_avg = df.loc[0, [f"{x}_avg" for x in stat_keys]].reset_index(drop=True)

    df_on = df.loc[0, [f"team_{x}" for x in stat_keys]].reset_index(drop=True)

    df_off = df.loc[0, [f"off_{x}" for x in stat_keys]].reset_index(drop=True)

    df_merged = pd.concat([pd.Series(stat_keys), df_self, df_avg, df_on, df_off], axis=1)

    df_merged.columns = ["stat", "self", "avg", "on", "off"]
    df_merged["avg"] = df_merged["avg"].astype(float).round(2)

    df_highlight = df.loc[:, highlight_stats]
    df_highlight.loc[:, highlight_stats[2:]] = df_highlight.loc[:,highlight_stats[2:]].astype(float).round(2)

    data = df_merged.to_dict("records")
    cols = [{"name": i, "id": i} for i in df_merged.columns]
    child = dash_table.DataTable(
        id='player-table-data',
        data=data,
        columns=cols,
        style_cell={"font_size": "10px",
                    "font_family": "sans-serif"},
        fill_width=False,
    )

    data_highlight = df_highlight.to_dict("records")
    cols_highlight = [{"name": i, "id": i} for i in df_highlight.columns]
    child_highlight = dash_table.DataTable(
        id='player-table-data',
        data=data_highlight,
        columns=cols_highlight,
        style_cell={"font_size": "10px",
                    "font_family": "sans-serif"},
        fill_width=False,
    )

    img_url = f"photos/{player_id}.png"

    return [html.Img(src=dash.get_asset_url(img_url), style={'height': '10%', 'width': '10%'}), child_highlight, child]
