import dash
import numpy as np
from dash import Dash, html, dcc, dash_table, callback, Output, Input, State
import plotly.express as px
import pandas as pd
import requests
import igviz as ig
import networkx as nx
import plotly.graph_objects as go

dash.register_page(__name__, path="/teams")


def layout():

    init_team = requests.get(f"http://euroleague-api:8989/SeasonTeams")
    init_team = init_team.json()
    init_team = pd.DataFrame.from_dict(init_team)

    options = {y: x for x, y in zip(init_team["team_name"], init_team["CODETEAM"])}

    layout_local = html.Div(children=[
        html.Div([html.Div(dcc.Dropdown(
            options=options,
            value=[],
            id="dropdown-team-index"

        ),
            style={"width": "50%"}),
            html.Button('Submit', id='submit-val-team-index', n_clicks=0)], style={"display": "flex",
                                                                             "flex-direction": "row",
                                                                             "width": "50%"}),
        dcc.Location(id="location-team-index")
    ])
    return layout_local


@callback(
    Output("location-team-index", "pathname"),
    State(component_id="dropdown-team-index", component_property="value"),
    Input(component_id="submit-val-team-index", component_property="n_clicks"),
    prevent_initial_call=True
)
def navigate_to_url(val, n_clicks):
    return f"/teams/{val}"


