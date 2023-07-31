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
    team_id_store = dcc.Store(id="team-code-store", data=team_code)
    team_data_store = dcc.Store(id="team-data-store", data=[])
    team_points_store = dcc.Store(id="team-points-store", data=[])
    court_figure_df = dcc.Store(id="court-figure-store", data=features.to_json(orient="split"))

    layout_local = html.Div(children=[
        team_id_store,
        team_data_store,
        team_points_store,
        court_figure_df,
        html.Div(id="team-header", children=[], style={"display":"flex",
                                                       "flex-direction": "row"})

    ])
    return layout_local


@callback(
    Output(component_id="team-header", component_property="children"),
    Input(component_id="team-code-store", component_property="data"),
    Input(component_id="court-figure-store", component_property="data"),
    Input(component_id="team-points-store", component_property="data")

)
def update_team_header(team_code, court_df, points):
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
        yaxis="y"
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
        style={"width": "25%"})

    return [html.Img(src=dash.get_asset_url(team_img_url), style={"height": "100%"}),
            chart]


@callback(
    Output(component_id="team-data-store", component_property="data"),
    Input(component_id="team-code-store", component_property="data")
)
def call_teams_agg_api(team_code):
    response = requests.get(f"http://euroleague-api:8989/Teams?team={team_code}")
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





