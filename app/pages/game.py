import dash
import numpy as np
from dash import Dash, html, dcc, dash_table, callback, Output, Input, State
import plotly.express as px
import pandas as pd
import requests
import igviz as ig
import networkx as nx
import plotly.graph_objects as go

dash.register_page(__name__, path_template="/game/<game_code>")
features = pd.read_csv("assets/features.csv")


def layout(game_code=1):
    game_id_store = dcc.Store(id="game-code-store", data=game_code)
    json_store = dcc.Store(id="json-store", data={})
    json_store_team = dcc.Store(id="json-store-teams", data={})
    json_store_points = dcc.Store(id="json-store-points", data={})
    json_store_assists = dcc.Store(id="json-store-assists", data={})
    key_stats_table_store = dcc.Store(id="key-stats-table-store", data={})
    key_stats_json = dcc.Store(id="key-stats-json", data=[])
    court_figure_df = dcc.Store(id="court-figure-store", data=features.to_json(orient="split"))

    layout_local = html.Div(
        children=[

            html.Div(["Enter game code",
                      dcc.Input(id="game-code-input", type="number", value=game_code),
                      html.Button('Submit', id='submit-val-game', n_clicks=0)], style={"display": "flex",
                                                                                       "flex-direction": "row",
                                                                                       "width": "50%"})
            ,
            dcc.Location(id="location-game"),
            game_id_store,
            json_store,
            json_store_team,
            json_store_points,
            json_store_assists,
            key_stats_table_store,
            key_stats_json,
            court_figure_df,
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
            html.Div(id="box-score", children=[], style={
                "display": "flex",
                "align-items": "flex-start",
                "justify-content": "center"}),
            html.Div(id="assist-charts", children=[], style={
                "display": "flex",
                "align-items": "flex-start",
                "justify-content": "center"})
        ],
        style={"display": "flex",
               "flex-direction": "column",
               "justify-content": "center",
               }

    )

    return layout_local


@callback(
    Output(component_id="json-store", component_property="data"),
    Input(component_id="game-code-store", component_property="data")
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
    Output(component_id="json-store-teams", component_property="data"),
    Input(component_id="game-code-store", component_property="data")
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
    df["home"] = df["home"].astype(bool)

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


@callback(Output('key-stats-table-store', 'data'),
          Input('key-stats-json', 'data'))
def update_key_stats_output(json_df):
    info_dataframe = pd.read_json(json_df, orient='split')

    data = info_dataframe.to_dict("records")
    cols = [{"name": i, "id": i} for i in info_dataframe.columns]

    child = dash_table.DataTable(
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

    return child


@callback(
    Output(component_id="json-store-points", component_property="data"),
    Input(component_id="game-code-store", component_property="data")
)
def call_points_single_game_api(game_code):
    response = requests.get(f"http://euroleague-api:8989/PointsSingleGame?game_code={game_code}")
    response = response.json()
    return response


@callback(
    Output(component_id="key-stats", component_property="children"),
    [Input(component_id="json-store-points", component_property="data"),
     Input(component_id="key-stats-table-store", component_property="data"),
     Input(component_id="court-figure-store", component_property="data")

     ]
)
def plot_points(response, key_stats_df, court_df):
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

    df_home = df.loc[df["home"], :]
    df_away = df.loc[~df["home"], :]

    fig_home = fig.add_trace(go.Histogram2dContour(
        x=df_home["COORD_X"].tolist(),
        y=df_home["COORD_Y"].tolist(),
        colorscale=['rgb(255, 255, 255)'] + px.colors.sequential.Magma[1:][::-1],
        showscale=False,
        line=dict(width=0),
        hoverinfo='none',
        xaxis="x",
        yaxis="y"
    )).add_trace(
        go.Scatter(x=df_home["COORD_X"].tolist(),
                   y=df_home["COORD_Y"].tolist(),
                   mode='markers',
                   marker=dict(
                       symbol=df_home["marker"].tolist(),
                       color='black',
                       size=7,

                   ),
                   xaxis="x",
                   yaxis="y",
                   hoverinfo='none',
                   customdata=np.stack((df_home['PLAYER'], df_home['ID_ACTION']), axis=-1),
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

    fig = go.Figure()

    for x in court_df["type"].unique().tolist():
        fig.add_trace(
            go.Scatter(x=features.loc[features["type"] == x, "y"],
                       y=features.loc[features["type"] == x, "x"],
                       marker={"color": "black"}))

    fig.update_traces(showlegend=False)

    fig_away = fig.add_trace(go.Histogram2dContour(
        x=df_away["COORD_X"].tolist(),
        y=df_away["COORD_Y"].tolist(),
        colorscale=['rgb(255, 255, 255)'] + px.colors.sequential.Magma[1:][::-1],
        showscale=False,
        line=dict(width=0),
        hoverinfo='none',
        xaxis="x",
        yaxis="y"
    )).add_trace(
        go.Scatter(x=df_away["COORD_X"].tolist(),
                   y=df_away["COORD_Y"].tolist(),
                   mode='markers',
                   marker=dict(
                       symbol=df_away["marker"].tolist(),
                       color='black',
                       size=7
                   ),
                   xaxis="x",
                   yaxis="y",
                   hoverinfo='none',
                   customdata=np.stack((df_away['PLAYER'], df_away['ID_ACTION']), axis=-1),
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

    chart_home = html.Div(dcc.Graph(
        figure=fig_home,
        id="points-home"),
        style={"width": "25%"})
    chart_away = html.Div(dcc.Graph(
        figure=fig_away,
        id="points-away"),
        style={"width": "25%"})

    return [chart_home, key_stats_df, chart_away]


@callback(
    Output(component_id="box-score", component_property="children"),
    Input(component_id="json-store", component_property="data")
)
def update_boxscore(response):
    df = pd.DataFrame.from_dict(response)

    rp_quantile = requests.get(f"http://euroleague-api:8989/Quantile?type_quantile=player")
    rp_quantile = rp_quantile.json()

    df_quantile = pd.DataFrame.from_dict(rp_quantile)
    quantiles = df_quantile["quantiles"].loc[0]

    df["2FGA"] = df["2FGA"].replace(0, np.nan).astype("Int64")
    df["3FGA"] = df["3FGA"].replace(0, np.nan).astype("Int64")
    df["FTA"] = df["FTA"].replace(0, np.nan).astype("Int64")
    df["PF"] = df["CM"] + df["CMT"] + df["CMU"] + df["OF"]
    df["2FG"] = df["2FGM"].astype(str) + "/" + df["2FGA"].astype(str) + " (" + (100 * df['2FGM'] / df['2FGA']).round(
        1).astype(str) + "%)"
    df["3FG"] = df["3FGM"].astype(str) + "/" + df["3FGA"].astype(str) + " (" + (100 * df['3FGM'] / df['3FGA']).round(
        1).astype(str) + "%)"
    df["FT"] = df["FTM"].astype(str) + "/" + df["FTA"].astype(str) + " (" + (100 * df['FTM'] / df['FTA']).round(
        1).astype(str) + "%)"
    df["DREB"] = df["D"].astype(str) + " (" + (100 * df['DREBR']).round(1).astype(str) + "%)"
    df["OREB"] = df["O"].astype(str) + " (" + (100 * df['OREBR']).round(1).astype(str) + "%)"
    df["USG"] = (100 * df["usage"]).round(1).astype(str) + "%"
    df["PER"] = (df["PER"]).round(1)
    df["tmp"] = df["duration"] % 60
    df["tmp"] = df.apply(lambda x: f"0{x['tmp']}" if x["tmp"] < 10 else f"{x['tmp']}", axis=1)
    df["MIN"] = (df["duration"].fillna(0) / 60).astype(int).astype(str) + ":" + df["tmp"]
    df["TREB"] = df["D"] + df["O"]

    df = df.replace(0, np.nan)

    df.loc[df["2FGA"].isna(), "2FG"] = np.nan
    df.loc[df["3FGA"].isna(), "3FG"] = np.nan
    df.loc[df["FTA"].isna(), "FT"] = np.nan

    df = df.copy()

    df["Name"] = "<a href='" + "/players/" + df["PLAYER_ID"] + "' style='vertical-align: middle '>" + df[
        "playerName"] + "</a>"

    df = df[
        ["Name", "MIN", "pts", "USG", "2FG", "3FG", "FT", "DREB", "OREB", "TREB", "AS", "TO", "ST", "FV", "PF", "RV",
         "PIR", "PER",
         "home"]]

    df_home = df.loc[df["home"], :]
    df_away = df.loc[~df["home"], :]

    del df_home["home"]
    del df_away["home"]

    df_dict_home = df_home.to_dict("records")
    df_dict_away = df_away.to_dict("records")

    cols = [{"name": i, "id": i} for i in df_home.columns[1:]]
    cols.insert(0, {"name": "Name", "id": "Name", "presentation": "markdown"})
    child_home = dash_table.DataTable(
        id='box-score-table-home',
        data=df_dict_home,
        columns=cols,
        style_cell={"font_size": "10px",
                    "font_family": "sans-serif"},
        fill_width=False,
        markdown_options={"html": True},
        style_data_conditional=[
            {"if": {"column_id": "pts"},
             "font-weight": "bold",
             "text-align": "center"},
            {"if": {"column_id": "Name"},
             "verticalAlign": "middle"},
            {"if": {"column_id": "PIR"},
             "font-weight": "bold"}
            ,
            {"if": {"column_id": "PIR",
                    "filter_query": "{PIR} <= " + f"{quantiles[0]}"},
             "color": "#9d9d9d"
             },
            {"if": {"column_id": "PIR",
                    "filter_query": "{PIR} >" + f"{quantiles[0]}" + " && {PIR} <= " + f"{quantiles[1]}"},
             "color": "#1eff00"
             },
            {"if": {"column_id": "PIR",
                    "filter_query": "{PIR} > " + f"{quantiles[1]}" + " && {PIR} <= " + f"{quantiles[2]}"},
             "color": "#0070dd"
             },
            {"if": {"column_id": "PIR",
                    "filter_query": "{PIR} > " + f"{quantiles[2]}" + " && {PIR} <= " + f"{quantiles[3]}"},
             "color": "#a335ee"
             },
            {"if": {"column_id": "PIR",
                    "filter_query": "{PIR} > " + f"{quantiles[3]}" + " && {PIR} <= " + f"{quantiles[4]}"},
             "color": "#ff8000"
             }

        ],
        style_data={"text-align": "center",
                    "border-left-color": "#F9F9F9",
                    "border-right-color": "#F9F9F9",
                    "border-left-width": "1px thin",
                    "border-right-width": "1px thin"
                    },
        style_header={"textAlign": "center"}

    )

    child_away = dash_table.DataTable(
        id='box-score-table-away',
        data=df_dict_away,
        columns=cols,
        # style_header={"display": "none"},
        style_cell={"font_size": "10px",
                    "font_family": "sans-serif"},
        fill_width=False,
        markdown_options={"html": True},
        style_data_conditional=[
            {"if": {"column_id": "pts"},
             "font-weight": "bold",
             "text-align": "center"},
            {"if": {"column_id": "Name"},
             "verticalAlign": "middle"
             },
            {"if": {"column_id": "PIR"},
             "font-weight": "bold"}
            ,
            {"if": {"column_id": "PIR",
                    "filter_query": "{PIR} <= " + f"{quantiles[0]}"},
             "color": "#9d9d9d"
             },
            {"if": {"column_id": "PIR",
                    "filter_query": "{PIR} > " + f"{quantiles[0]}" + " && {PIR} <= " + f"{quantiles[1]}"},
             "color": "#1eff00"
             },
            {"if": {"column_id": "PIR",
                    "filter_query": "{PIR} > " + f"{quantiles[1]}" + " && {PIR} <= " + f"{quantiles[2]}"},
             "color": "#0070dd"
             },
            {"if": {"column_id": "PIR",
                    "filter_query": "{PIR} > " + f"{quantiles[2]}" + " && {PIR} <= " + f"{quantiles[3]}"},
             "color": "#a335ee"
             },
            {"if": {"column_id": "PIR",
                    "filter_query": "{PIR} > " + f"{quantiles[3]}" + " && {PIR} <= " + f"{quantiles[4]}"},
             "color": "#ff8000"
             }
        ],
        style_data={"text-align": "center",
                    "border-left-color": "#F9F9F9",
                    "border-right-color": "#F9F9F9",
                    "border-left-width": "1px thin",
                    "border-right-width": "1px thin"

                    },
        style_header={"textAlign": "center"}

    )

    return [child_home, html.Div(style={"width": "5%"}), child_away]


@callback(
    Output(component_id="json-store-assists", component_property="data"),
    Input(component_id="game-code-store", component_property="data")
)
def call_assists_api(game_code):
    response = requests.get(f"http://euroleague-api:8989/AssistsSingleGame?game_code={game_code}")
    response = response.json()
    return response


@callback(
    Output(component_id="assist-charts", component_property="children"),
    Input(component_id="json-store-assists", component_property="data"),
)
def plot_assist_charts(response):
    def createDiGraph(df, players):
        # Create a directed graph (digraph) object; i.e., a graph in which the edges
        # have a direction associated with them.
        G = nx.DiGraph()

        # Add nodes:
        nodes = players
        G.add_nodes_from(nodes)

        # Add edges or links between the nodes:
        edges = [(x, y) for x, y in zip(df["playerNameAssisting"], df["playerName"])]
        edge_labels = {tup: lab for tup, lab in zip(edges, df["count"])}
        node_labels = {x: x for x in nodes}

        G.add_edges_from(edges)
        nx.set_edge_attributes(G, edge_labels, "edge_prop")
        nx.set_node_attributes(G, node_labels, "node_prop")

        return G

    df = pd.DataFrame.from_dict(response)
    df["count"] = 1

    df = df.groupby(["playerNameAssisting", "playerName", "home"]).agg({"count": "sum"}).reset_index()

    df_home = df.loc[df["home"], :]
    df_away = df.loc[~df["home"], :]

    del df_home["home"]
    del df_away["home"]

    players_home = pd.concat([df_home["playerNameAssisting"], df_home["playerName"]]).unique()
    players_away = pd.concat([df_away["playerNameAssisting"], df_away["playerName"]]).unique()

    home_graph = createDiGraph(df_home, players_home)
    away_graph = createDiGraph(df_away, players_away)

    home_plot = ig.plot(home_graph, size_method="static",
                        color_method="#ffcccb",
                        edge_label="edge_prop",
                        node_label="node_prop",
                        edge_label_position="bottom center",
                        layout="circular").update_traces(marker_showscale=False).update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )

    away_plot = ig.plot(away_graph, size_method="static",
                        color_method="#164E9B",
                        edge_label="edge_prop",
                        edge_label_position="bottom center",
                        node_label="node_prop",
                        layout="circular").update_traces(marker_showscale=False).update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )

    return [dcc.Graph(figure=home_plot), html.Div(style={"width": "5%"}), dcc.Graph(figure=away_plot)]


@callback(
    Output("location-game", "pathname"),
    State(component_id="game-code-input", component_property="value"),
    Input(component_id="submit-val-game", component_property="n_clicks")

)
def navigate_to_game_url(val, n_clicks):
    return f"/game/{val}"
