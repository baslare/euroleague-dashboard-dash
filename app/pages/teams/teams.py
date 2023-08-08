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

dash.register_page(__name__, path_template="/teams/<team_code>")
features = pd.read_csv("assets/features.csv")


def layout(team_code="MAD"):
    init_team = requests.get(f"http://euroleague-api:8989/SeasonTeams")
    init_team = init_team.json()
    init_team = pd.DataFrame.from_dict(init_team)

    options = {y: x for x, y in zip(init_team["team_name"], init_team["CODETEAM"])}

    team_id_store = dcc.Store(id="team-code-store", data=team_code)
    team_data_store = dcc.Store(id="team-data-store", data=[])
    team_points_store = dcc.Store(id="team-points-store", data=[])
    team_players_store = dcc.Store(id="team-players-store", data=[])
    court_figure_df = dcc.Store(id="court-figure-store", data=features.to_json(orient="split"))

    layout_local = html.Div(children=[
        html.Div([html.Div(dcc.Dropdown(
            options=options,
            value=team_code,
            id="dropdown-team"

        ),
            style={"width": "80%"}),
            html.Button('Submit', id='submit-val-team', n_clicks=0)], className="dropdown-top"),
        dcc.Location(id="location-team"),
        team_id_store,
        team_data_store,
        team_points_store,
        team_players_store,
        court_figure_df,
        html.Div(id="team-header", children=[], className="team-header"),
        html.Div(id="team-players-table", children=[], style={"width": "85%"})

    ],
        style={"display": "flex",
               "flex-direction": "column",
               "justify-content": "center",
               "align-items": "center"})


    return layout_local


@callback(
    Output(component_id="team-header", component_property="children"),
    Input(component_id="team-code-store", component_property="data"),
    Input(component_id="court-figure-store", component_property="data"),
    Input(component_id="team-points-store", component_property="data"),
    Input(component_id="team-data-store", component_property="data")

)
def update_team_header(team_code, court_df, points, response_team):
    team_img_url = f"{team_code}.png"

    df = pd.DataFrame.from_dict(points)
    court_df = pd.read_json(court_df, orient='split')

    fig = go.Figure()

    for x in court_df["type"].unique().tolist():
        fig.add_trace(
            go.Scatter(x=features.loc[features["type"] == x, "y"],
                       y=features.loc[features["type"] == x, "x"],
                       marker={"color": "black"}))

    fig.update_traces(showlegend=False)

    df["marker"] = np.where(df["missed"], "x", "circle-open")

    fig = fig.add_trace(go.Histogram2dContour(
        x=df["COORD_X"].tolist(),
        y=df["COORD_Y"].tolist(),
        colorscale=['rgb(255, 255, 255)'] + px.colors.sequential.Purp[1:][::-1],
        showscale=False,
        line=dict(width=0),
        hoverinfo='none',
        xaxis="x",
        yaxis="y",

        nbinsx=30,
        nbinsy=30
    )).add_trace(
        go.Scatter(x=df["COORD_X"].tolist(),
                   y=df["COORD_Y"].tolist(),
                   opacity=0.2,
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

    chart = html.Div(dcc.Graph(
        figure=fig,
        id="points-team"),
        className="points",
        style={"width": "35%"})

    df_team = pd.DataFrame(response_team, index=[0])

    highlight_stats = ["CODETEAM", "2FGM", "2FGA", "2FGR", "2FGR_rank", "as2P",
                       "3FGM", "3FGA", "3FGR", "3FGR_rank", "as3P",
                       "FG", "FG_rank", "FT_four", "FT_rank",
                       "ORtg", "ORtg_rank", "DRtg", "DRtg_rank",
                       "AS_avg", "AS_rank", "TO_avg", "TOR", "TOR_rank",
                       "D_avg", "DREBR", "DREB_rank",
                       "O_avg", "OREBR", "OREB_rank",
                       "pace", "pace_rank"]

    non_pct_stats = ["ORtg", "DRtg", "pace", "AS_avg", "D_avg", "O_avg", "TO_avg"]

    pct_stats = ["2FGR", "as2P", "3FGR", "as3P", "FG", "FT_four", "TOR", "DREBR", "OREBR"]

    df_team.loc[:, pct_stats] = (100 * df_team[pct_stats]).astype(np.float64).round(1).astype(
        str) + "%"

    df_team.loc[:, non_pct_stats] = df_team[non_pct_stats].astype(np.float64).round(1)

    df_team = df_team[highlight_stats]

    left_index = [1, 6, 11, 15, 19, 24, 27, 30]
    right_index = [6, 11, 15, 19, 24, 27, 30, 32]
    df_list = []
    for i, j in zip(left_index, right_index):
        df_list.append(df_team.loc[:, highlight_stats[i:j]])

    def generate_dash_elements(item):
        data_row = item.to_dict("records")
        col_row = [{"name": col, "id": col} for col in item.columns]

        table = dash_table.DataTable(
            data=data_row,
            columns=col_row,
            style_cell={
                        "font_family": "sans-serif",
                        "text-align": "center"},
            style_header={
                          "font_family": "sans-serif",
                          "text-align": "center"},

        )

        return html.Div(children=table)

    children_list = []

    for x in df_list:
        children_list.append(generate_dash_elements(x))

    stats_wrapper = html.Div(children=children_list,
                             className="stats-wrapper"

                                    )

    return [html.Img(src=dash.get_asset_url(team_img_url), className="team-logo"),
            chart,
            stats_wrapper]


@callback(
    Output(component_id="team-data-store", component_property="data"),
    Input(component_id="team-code-store", component_property="data")
)
def call_teams_agg_api(team_code):
    response = requests.get(f"http://euroleague-api:8989/Team?team={team_code}")
    response = response.json()
    return response


@callback(
    Output(component_id="team-points-store", component_property="data"),
    Input(component_id="team-code-store", component_property="data")
)
def call_team_points_api(team_code):
    response = requests.get(f"http://euroleague-api:8989/PointsTeam?team={team_code}")
    response = response.json()
    return response


@callback(
    Output(component_id="team-players-store", component_property="data"),
    Input(component_id="team-code-store", component_property="data")
)
def call_team_players_api(team_code):
    response = requests.get(f"http://euroleague-api:8989/Player?team={team_code}")
    response = response.json()
    return response

@callback(
    Output(component_id="team-players-table", component_property="children"),
    Input(component_id="team-players-store", component_property="data")
)

def update_team_players_table(response):

    df = pd.DataFrame.from_dict(response)

    rp_quantile = requests.get(f"http://euroleague-api:8989/Quantile?type_quantile=player_agg")
    rp_quantile = rp_quantile.json()

    df_quantile = pd.DataFrame.from_dict(rp_quantile)
    quantiles = df_quantile["quantiles"].loc[0]

    df["as2P"] = df["assisted_2fg"] / df["2FGM"]
    df["as3P"] = df["assisted_3fg"] / df["3FGM"]
    df["tmp"] = (df["duration_avg"] % 60).astype(int)
    df["tmp"] = df.apply(lambda row: f"0{row['tmp']}" if row["tmp"] < 10 else f"{row['tmp']}", axis=1)
    df["MPG"] = (df["duration_avg"] / 60).astype(int).astype(str) + ":" + df["tmp"]

    highlight_stats = ["Name", "p",
                       "game_count", "MPG", "pts_avg", "PER_season", "PIR_avg",
                       "2FGP", "3FGR", "FTR", "ORtg_avg", "usage",
                       "AS_avg", "TO_avg", "as2P", "as3P", "eFG",
                       "REB_avg", "D_avg", "O_avg", "DREBR", "OREBR",
                        "plus_minus_avg", "FV_avg", "ST_avg",
                       ]

    highlight_cols = ["Name", "p",
                      "G", "MPG", "pts", "PER", "PIR",
                      "2FG%", "3FG%", "FT%", "ORTG", "USG%",
                      "AS", "TO", "a2P%", "a3P%", "eFG%",
                      "REB", "D", "O", "D%", "O%",
                       "+/-", "BL", "ST",
                      ]

    non_pct_cols = ["pts", "PER", "PIR",
                    "FT%", "ORTG",
                    "AS", "TO",
                    "REB", "D", "O",
                     "+/-", "BL", "ST"]

    pct_cols = ["2FG%", "3FG%", "FT%", "D%", "O%", "USG%", "a2P%", "a3P%", "eFG%"]

    df["Name"] = "<a href='" + "/players/" + df["PLAYER_ID"] + "' style='vertical-align: middle '>" + df[
        "playerName"] + "</a>"



    df_highlight = df.loc[:, highlight_stats]
    df_highlight.columns = highlight_cols

    df_highlight.loc[:, non_pct_cols] = df_highlight.loc[:, non_pct_cols].astype(np.float64).round(1)

    df_highlight.loc[:,pct_cols] = (100 * df_highlight[pct_cols]).astype(np.float64).round(1).astype(str) + "%"
    df_highlight.loc[:,pct_cols] = df_highlight[pct_cols].replace("nan%", np.nan)

    df_highlight = df_highlight.sort_values("PER", ascending=False)

    cols = [{"name": i, "id": i} for i in df_highlight.columns[1:]]
    cols.insert(0, {"name": "Name", "id": "Name", "presentation": "markdown"})

    table = dash_table.DataTable(
        data=df_highlight.to_dict("records"),
        columns= cols,
        style_cell={
                    "font_family": "sans-serif",
                    "text-align": "center"},
        style_header={
                      "font_family": "sans-serif",
                      "text-align": "center"},
        style_as_list_view=True,
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

        ]

    )

    return  table





@callback(
    Output("location-team", "pathname"),
    State(component_id="dropdown-team", component_property="value"),
    Input(component_id="submit-val-team", component_property="n_clicks"),
)
def navigate_to_url(val, n_clicks):
    return f"/teams/{val}"
