import json
import numpy as np
import dash_bootstrap_components as dbc
import dash
from dash import Dash, html, dcc, dash_table, callback, Output, Input, State
from dash.exceptions import PreventUpdate
import plotly.express as px
import pandas as pd
import requests
import plotly.graph_objects as go

dash.register_page(__name__, path_template="/players/<player_id>")
features = pd.read_csv("assets/features.csv")
court_figure_df = dcc.Store(id="court-figure-store", data=features.to_json(orient="split"))


def layout(player_id="PTGB"):
    id_store = dcc.Store(id="player-id-store", data=player_id)
    json_store_player = dcc.Store(id="json-store-player", data=[])
    json_store_points = dcc.Store(id="json-store-points-player", data=[])
    json_store_source = dcc.Store(id="json-store-source", data=[])
    json_store_target = dcc.Store(id="json-store-target", data=[])
    points_plot_store = dcc.Store(id="points-plot-store", data=[])

    layout_local = html.Div(

        children=[
            court_figure_df,
            json_store_points,
            json_store_player,
            id_store,
            json_store_target,
            json_store_source,
            points_plot_store,
            html.Div(id="player-highlights",
                     children=[],
                     style={"display": "flex",
                            "flex-direction": "row",
                            "width": "50%"}),
            html.Div(id="points-plot", children=[], style={"display":"flex",
                                                           "flex-direction":"row"}),
            html.Div(id="player-table", children=[])
        ],
        style={"display": "flex",
               "flex-direction": "column",
               "justify-content": "center",
               "align-items": "center"}

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
    Output(component_id="player-highlights", component_property="children"),
    Input(component_id="json-store-player", component_property="data"),
    Input(component_id="player-id-store", component_property="data")
)
def update_player_highlights(response, player_id):
    df = pd.DataFrame(response, index=[0])

    df["as2P"] = df["assisted_2fg"] / df["2FGM"]
    df["as3P"] = df["assisted_3fg"] / df["3FGM"]
    df["tmp"] = (df["duration_avg"] % 60).astype(int)
    df["tmp"] = df.apply(lambda x: f"0{x['tmp']}" if x["tmp"] < 10 else f"{x['tmp']}", axis=1)
    df["MPG"] = (df["duration_avg"] / 60).astype(int).astype(str) + ":" + df["tmp"]

    highlight_stats = ["playerName", "p", "CODETEAM",
                       "game_count", "MPG", "pts_avg", "PER_season", "PIR_avg",
                       "2FGP", "3FGR", "FTR", "ORtg_avg", "usage",
                       "AS_avg", "TO_avg", "as2P", "as3P", "eFG_avg",
                       "REB_avg", "D_avg", "O_avg", "DREBR", "OREBR",
                       "on_ORtg_avg", "off_ORtg_avg", "plus_minus_avg",
                       "on_DRtg_avg", "off_DRtg_avg", "FV_avg", "ST_avg",
                       ]

    highlight_cols = ["playerName", "p", "CODETEAM",
                      "G", "MPG", "pts", "PER", "PIR",
                      "2FG%", "3FG%", "FT%", "ORTG", "USG%",
                      "AS", "TO", "a2P%", "a3P%", "eFG%",
                      "REB", "D", "O", "D%", "O%",
                      "on_ORtg", "off_ORtg", "+/-",
                      "on_DRtg", "off_DRtg", "BL", "ST",
                      ]

    non_pct_cols = ["pts", "PER", "PIR",
                    "FT%", "ORTG",
                    "AS", "TO",
                    "REB", "D", "O",
                    "on_ORtg", "off_ORtg", "+/-",
                    "on_DRtg", "off_DRtg", "BL", "ST"]

    df_highlight = df.loc[:, highlight_stats]
    df_highlight.columns = highlight_cols

    df_highlight.loc[:, non_pct_cols] = df_highlight.loc[:, non_pct_cols].astype(np.float64).round(2)

    df_highlight[
        ["2FG%", "3FG%", "FT%", "D%", "O%", "USG%", "a2P%", "a3P%", "eFG%"]] = (100 * df_highlight[
        ["2FG%", "3FG%", "FT%", "D%", "O%", "USG%", "a2P%", "a3P%", "eFG%"]]).astype(np.float64).round(2).astype(
        str) + "%"

    left_index = [3, 8, 13, 18, 23, 26]
    right_index = [8, 13, 18, 23, 26, 30]
    df_list = []
    for i, j in zip(left_index, right_index):
        df_list.append(df_highlight.loc[:, highlight_cols[i:j]])

    def generate_dash_elements(item):
        data_row = item.to_dict("records")
        col_row = [{"name": i, "id": i} for i in item.columns]

        table = dash_table.DataTable(
            data=data_row,
            columns=col_row,
            style_cell={"font_size": "10px",
                        "font_family": "sans-serif",
                        "text-align": "center"},
            style_header={"font_size": "10px",
                          "font_family": "sans-serif",
                          "text-align": "center"},

        )

        return html.Div([html.Div(children=table, style={"height": "75%"}),
                         html.Div(style={"height": "10px"})],
                        style={"display": "flex",
                               "flex-direction": "column",
                               "width": "50%"})

    children_list = []

    for x in df_list:
        children_list.append(generate_dash_elements(x))

    stats_wrapper = html.Div(children=children_list,
                             style={"width": "50%"})

    img_url = f"photos/{player_id}.png"

    player_text = html.Div(children=[
        html.H4(f"{df_highlight['playerName'].loc[0]}", style={"vertical-align": "top"}),
        html.H6(f"{df_highlight['p'].loc[0]}", style={"vertical-align": "top"}),
        html.H6(f"{df_highlight['CODETEAM'].loc[0]}", style={"vertical-align": "top"})

    ],
        style={"display": "flex",
               "flex-direction": "column",
               "align-items": "center",
               "justify-content": "center",
               })

    header = html.Div(children=[html.Img(src=dash.get_asset_url(img_url), style={'width': '30%'}),
                                player_text],
                      style={"display": "flex",
                             "flex-direction": "row",
                             "align-items": "center",
                             "justify-content": "center",
                             "width": "50%"})

    return [header, stats_wrapper]


@callback(
    Output(component_id="player-table", component_property="children"),
    Input(component_id="json-store-player", component_property="data")

)
def update_player_table(response):
    df = pd.DataFrame(response, index=[0])

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

    return child


@callback(
    Output(component_id="json-store-points-player", component_property="data"),
    Input(component_id="player-id-store", component_property="data")

)
def call_players_points_api(player_id):
    response = requests.get(f"http://euroleague-api:8989/PointsPlayer?player_id={player_id}")
    response = response.json()
    return response


@callback(
    Output(component_id="points-plot-store", component_property="data"),
    Input(component_id="json-store-points-player", component_property="data"),
    Input(component_id="court-figure-store", component_property="data")

)
def plot_player_points(response, court_df):
    df = pd.DataFrame.from_dict(response)
    court_df = pd.read_json(court_df, orient='split')

    fig = go.Figure()

    for x in court_df["type"].unique().tolist():
        fig.add_trace(
            go.Scatter(x=features.loc[features["type"] == x, "y"],
                       y=features.loc[features["type"] == x, "x"],
                       marker={"color": "black"}))

    fig.update_traces(showlegend=False)

    df["marker"] = np.where(df["missed"], "x", "circle-open")

    fig.add_trace(go.Histogram2dContour(
        x=df["COORD_X"].tolist(),
        y=df["COORD_Y"].tolist(),
        colorscale=['rgb(255, 255, 255)'] + px.colors.sequential.Sunsetdark[1:][::-1],
        showscale=False,
        line=dict(width=0),
        hoverinfo='none',
        xaxis="x",
        yaxis="y"
    )).add_trace(
        go.Scatter(x=df["COORD_X"].tolist(),
                   y=df["COORD_Y"].tolist(),
                   mode='markers',
                   marker=dict(
                       symbol=df["marker"].tolist(),
                       color='black',
                       size=5,

                   ),
                   xaxis="x",
                   yaxis="y",
                   hoverinfo='none',
                   customdata=np.stack((df['PLAYER'], df['ID_ACTION']), axis=-1),
                   hovertemplate="<b>Player</b> %{customdata[0]} <br>" +
                                 "<b>Shot Type</b> %{customdata[1]}"
                   )).update_yaxes(
        range=[-200, 1200],
        gridcolor='White',
        scaleanchor="x",
        scaleratio=1,
    ).update_xaxes(
        range=[-800, 800],
        gridcolor='White').update_traces(showlegend=False).update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )

    chart = dcc.Graph(
        figure=fig,
        id="points-player-chart")

    return chart


@callback(
    Output(component_id="json-store-source", component_property="data"),
    Output(component_id="json-store-target", component_property="data"),
    Input(component_id="player-id-store", component_property="data"),

)
def call_assists_api(player_id):
    response_source = requests.get(f"http://euroleague-api:8989/AssistsPlayer?assisting_player={player_id}")
    response_source = response_source.json()

    response_target = requests.get(f"http://euroleague-api:8989/AssistsPlayer?player_id={player_id}")
    response_target = response_target.json()

    return response_source, response_target


@callback(
    Output(component_id="points-plot", component_property="children"),
    Input(component_id="points-plot-store", component_property="data"),
    Input(component_id="json-store-source", component_property="data"),
    Input(component_id="json-store-target", component_property="data"),

)
def update_plots(points_fig, response_source, response_target):
    df_source = pd.DataFrame.from_dict(response_source)
    df_target = pd.DataFrame.from_dict(response_target)

    # source plot
    df_source["count"] = 1

    df_source_left = df_source.groupby(["playerNameAssisting", "playerName"]).agg({"count": "sum"}).reset_index()
    df_source_right = df_source.groupby(["playerName", "PLAYTYPE"]).agg({"count": "sum"}).reset_index()

    df_source_left.columns = ["source", "target", "value"]
    df_source_right.columns = ["source", "target", "value"]

    sankey_df_source = pd.concat([df_source_left, df_source_right]).reset_index(drop=True)

    labels_source = pd.concat([sankey_df_source["source"], sankey_df_source["target"]]).unique()
    labels_source_dict = {x: y for x, y in zip(labels_source, range(len(labels_source)))}

    sankey_df_source["source"] = sankey_df_source["source"].map(labels_source_dict)
    sankey_df_source["target"] = sankey_df_source["target"].map(labels_source_dict)

    sankey_df_source = sankey_df_source.loc[(sankey_df_source["source"] != sankey_df_source["target"]), :]

    left_fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=labels_source,
            color="blue"
        ),
        link=dict(
            source=sankey_df_source["source"],
            target=sankey_df_source["target"],
            value=sankey_df_source["value"]
        ))])

    # target plot

    df_target["count"] = 1

    df_target_left = df_target.groupby(["playerNameAssisting", "playerName"]).agg({"count": "sum"}).reset_index()
    df_target_right = df_target.groupby(["playerName", "PLAYTYPE"]).agg({"count": "sum"}).reset_index()

    df_target_left.columns = ["source", "target", "value"]
    df_target_right.columns = ["source", "target", "value"]

    sankey_df_target = pd.concat([df_target_left, df_target_right]).reset_index(drop=True)

    labels_target = pd.concat([sankey_df_target["source"], sankey_df_target["target"]]).unique()
    labels_target_dict = {x: y for x, y in zip(labels_target, range(len(labels_target)))}

    sankey_df_target["source"] = sankey_df_target["source"].map(labels_target_dict)
    sankey_df_target["target"] = sankey_df_target["target"].map(labels_target_dict)

    sankey_df_target = sankey_df_target.loc[(sankey_df_target["source"] != sankey_df_target["target"]), :]

    right_fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=labels_target,
            color="blue"
        ),
        link=dict(
            source=sankey_df_target["source"],
            target=sankey_df_target["target"],
            value=sankey_df_target["value"]
        ))])

    children = [
        html.Div(dcc.Graph(
            figure=left_fig,
            id="sankey-left")),
        html.Div(points_fig),
        html.Div(dcc.Graph(
            figure=right_fig,
            id="sankey-right"))
    ]

    return children
