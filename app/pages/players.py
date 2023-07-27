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
    init_player = requests.get(f"http://euroleague-api:8989/InitPlayer")
    init_player = init_player.json()
    init_player = pd.DataFrame.from_dict(init_player)

    options = {y: x for x, y in zip(init_player["playerName"], init_player["PLAYER_ID"])}

    id_store = dcc.Store(id="player-id-store", data=player_id)
    json_store_player = dcc.Store(id="json-store-player", data=[])
    json_store_points = dcc.Store(id="json-store-points-player", data=[])
    json_store_source = dcc.Store(id="json-store-source", data=[])
    json_store_target = dcc.Store(id="json-store-target", data=[])
    points_plot_store = dcc.Store(id="points-plot-store", data=[])

    layout_local = html.Div(

        children=[html.Div([html.Div(dcc.Dropdown(
            options=options,
            value=player_id,
            id="dropdown-player"

        ),
            style={"width": "50%"}),
            html.Button('Submit', id='submit-val', n_clicks=0)], style={"display": "flex",
                                                                        "flex-direction": "row",
                                                                        "width": "50%"}),
            dcc.Location(id="location"),
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
                            "justify-content": "center",
                            "width": "80%",
                            "margin-top":"2%"
                            }),
            html.Div(id="points-plot", children=[], style={"display": "flex",
                                                           "flex-direction": "row"
                                                           }),
            html.Div(id="history-table", children=[], style={"width": "60%"}),
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
    Input(component_id="player-id-store", component_property="data"),
    Input(component_id="points-plot-store", component_property="data")
)
def update_player_highlights(response, player_id, points_plot):
    df = pd.DataFrame(response, index=[0])

    df["as2P"] = df["assisted_2fg"] / df["2FGM"]
    df["as3P"] = df["assisted_3fg"] / df["3FGM"]
    df["tmp"] = (df["duration_avg"] % 60).astype(int)
    df["tmp"] = df.apply(lambda row: f"0{row['tmp']}" if row["tmp"] < 10 else f"{row['tmp']}", axis=1)
    df["MPG"] = (df["duration_avg"] / 60).astype(int).astype(str) + ":" + df["tmp"]

    highlight_stats = ["playerName", "p", "CODETEAM",
                       "game_count", "MPG", "pts_avg", "PER_season", "PIR_avg",
                       "2FGP", "3FGR", "FTR", "ORtg_avg", "usage",
                       "AS_avg", "TO_avg", "as2P", "as3P", "eFG",
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
        col_row = [{"name": col, "id": col} for col in item.columns]

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
                               })

    children_list = []

    for x in df_list:
        children_list.append(generate_dash_elements(x))

    stats_wrapper = html.Div(children=children_list,
                             style={"width": "20%"

                                    })

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
               "margin-left": "5%"
               })

    df_ranks = df[["MPG_rank", "PPG_rank", "PIR_rank",
                   "PER_rank", "EFG_rank", "USG_rank"]]

    df_ranks = df_ranks.round(1)
    df_ranks.columns = ["MPG", "PPG", "PIR", "PER", "EFG", "USG"]
    data_ranks = df_ranks.to_dict("records")

    col_ranks = [{"name": i, "id": i} for i in df_ranks.columns]

    def highlight_ranks(df_local):

        conditional_dict = [[{"if": {"column_id": col,
                                     "filter_query": "{" + col + "}  <= " + f"25"},
                              "color": "#9d9d9d"
                              },
                             {"if": {"column_id": col,
                                     "filter_query": "{" + col + "} >" + f"25" + " && {" + col + "} <= " + f"50"},
                              "color": "#1eff00"
                              },
                             {"if": {"column_id": col,
                                     "filter_query": "{" + col + "} > " + f"50" + " && {" + col + "} <= " + f"75"},
                              "color": "#0070dd"
                              },
                             {"if": {"column_id": col,
                                     "filter_query": "{" + col + "} > " + f"75" + " && {" + col + "} <= " + f"95"},
                              "color": "#a335ee"
                              },
                             {"if": {"column_id": col,
                                     "filter_query": "{" + col + "} > " + f"95" + " && {" + col + "} <= " + f"100"},
                              "color": "#ff8000"
                              }] for col in df_local.columns]

        conditional_dict = sum(conditional_dict, [])

        return conditional_dict

    rank_table = dash_table.DataTable(
        data=data_ranks,
        columns=col_ranks,
        style_cell={"font_size": "14px",
                    "font_family": "sans-serif",
                    "text-align": "center",
                    "background-color": '#363636',
                    "font-weight": "bold"},
        style_header={"font_size": "12px",
                      "font_family": "sans-serif",
                      "text-align": "center",
                      "color": "white"},
        style_data_conditional=highlight_ranks(df_ranks),
        fill_width=True,

    )

    rank_table = html.Div(rank_table, style={"width": "90%", "margin-top": "5%"})

    header = html.Div(children=[html.Img(src=dash.get_asset_url(img_url), style={'width': '33%',
                                                                                 "border": "solid",
                                                                                 "border-width": "thin"}),
                                player_text],
                      style={"display": "flex",
                             "flex-direction": "row",
                             "align-items": "center",
                             "justify-content": "center"
                             })

    player_bio = html.Div(children=[header,
                                    rank_table],
                          style={"display": "flex",
                                 "flex-direction": "column",
                                 "width": "30%",
                                 "align-items": "center",
                                 "justify-content": "center"
                                 })

    return [player_bio, stats_wrapper, html.Div(points_plot, style={"width": "30%"})]


@callback(
    Output(component_id="player-table", component_property="children"),
    Input(component_id="json-store-player", component_property="data")

)
def update_player_table(response):
    df = pd.DataFrame(response, index=[0])

    stat_keys = ["AS", "TO", "3FGM", "3FGA", "2FGA", "2FGM",
                 "FTM", "FTA", "D", "O", "REB",
                 "RV", "CM", "FV", "AG", "ST", "OF", "CMT", "CMU", "CMD",
                 "multi_ft", "multi_ft_count", "tech_ft", "assisted_2fg", "assisted_3fg",
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
    Input(component_id="json-store-source", component_property="data"),
    Input(component_id="json-store-target", component_property="data"),

)
def update_plots(response_source, response_target):
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
            line=dict(width=0.5),
            label=labels_source,
            color="#F6BD60"
        ),
        link=dict(
            source=sankey_df_source["source"],
            target=sankey_df_source["target"],
            value=sankey_df_source["value"],
            color="#84A59D"
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
            line=dict(width=0.5),
            label=labels_target,
            color="#F7EDE2"
        ),
        link=dict(
            source=sankey_df_target["source"],
            target=sankey_df_target["target"],
            value=sankey_df_target["value"],
            color="#F28482"
        ))])

    children = [
        html.Div(dcc.Graph(
            figure=left_fig,
            id="sankey-left")),
        html.Div(dcc.Graph(
            figure=right_fig,
            id="sankey-right"))
    ]

    return children


@callback(
    Output("location", "pathname"),
    State(component_id="dropdown-player", component_property="value"),
    Input(component_id="submit-val", component_property="n_clicks"),
)
def navigate_to_url(val, n_clicks):
    return f"/players/{val}"


@callback(
    Output(component_id="history-table", component_property="children"),
    Input(component_id="player-id-store", component_property="data")
)
def update_history_table(player_id):
    response_history = requests.get(f"http://euroleague-api:8989/GamePlayers?player_id={player_id}")
    response_history = response_history.json()
    df_history = pd.DataFrame.from_dict(response_history)

    game_codes = df_history["game_code"].tolist()
    team_codes = df_history["CODETEAM"].unique().tolist()

    game_query_string = "?team=" + "&team=".join([str(x) for x in team_codes]) + \
                        "".join([f"&game_code={str(x)}" for x in game_codes])

    response_game_results = requests.get(f"http://euroleague-api:8989/Game{game_query_string}")
    response_results = response_game_results.json()

    df_results = pd.DataFrame.from_dict(response_results)

    df_history = df_history.merge(df_results[["game_code", "points_scored", "opp_points_scored"]], how="left",
                                  on="game_code")

    df_history["game"] = "<a href='" + "/game/" + df_history["game_code"].astype(str) + "'>" + df_history[
        "CODETEAM"] + " " + df_history["points_scored"].astype(str) + " - " + df_history["opp_points_scored"].astype(
        str) + " " + df_history["OPP"] + "</a>"

    df_history["duration"] = df_history["duration"].fillna(0)
    df_history["tmp"] = (df_history["duration"] % 60).astype(int)
    df_history["tmp"] = df_history.apply(lambda x: f"0{x['tmp']}" if x["tmp"] < 10 else f"{x['tmp']}", axis=1)
    df_history["MIN"] = (df_history["duration"].fillna(0) / 60).astype(int).astype(str) + ":" + df_history["tmp"]

    df_history = df_history[
        ["game", 'MIN', 'pts', 'AS', 'REB', 'PIR', 'PER', 'usage', '2FGM', '2FGA', '3FGA', '3FGM', 'FTM', 'FTA', 'ST',
         'FV', 'DREBR', 'OREBR', 'home']]
    df_history[["usage", "OREBR", "DREBR"]] = 100 * df_history[["usage", "OREBR", "DREBR"]]
    df_history[["PER", "usage", "OREBR", "DREBR"]] = df_history[["PER", "usage", "OREBR", "DREBR"]].round(2)

    df_history[["usage", "OREBR", "DREBR"]] = df_history[["usage", "OREBR", "DREBR"]].astype(str) + "%"

    data = df_history.to_dict("records")

    cols = [{"name": i, "id": i} for i in df_history.columns[1:]]
    cols.insert(0, {"name": "game", "id": "game", "presentation": "markdown"})

    child = dash_table.DataTable(
        id='history-table-data',
        data=data,
        columns=cols,
        style_cell={"font_size": "10px",
                    "font_family": "sans-serif",
                    "text-align": "center"},
        style_header={"font_size": "10px",
                      "font_family": "sans-serif",
                      "text-align": "center"},

        style_as_list_view=True,
        markdown_options={"html": True}
    )

    return child
