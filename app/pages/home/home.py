import dash
import numpy as np
from dash import Dash, html, dcc, dash_table, callback, Output, Input, State
import plotly.express as px
import pandas as pd
import requests
import igviz as ig
import networkx as nx
import plotly.graph_objects as go

dash.register_page(__name__, path="/")

def layout():
    layout_local = html.Div(
        children=[
            html.H2("This is the home page! Welcome")],
        style={"text-align": "center",
               "margin-top": "5rem"}

    )

    return layout_local
