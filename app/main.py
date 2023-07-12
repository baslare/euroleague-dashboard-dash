import dash
import dash_bootstrap_components as dbc
from dash import Dash, html, dcc, dash_table, callback, Output, Input, State


app = Dash(__name__, use_pages=True,  external_stylesheets=[dbc.themes.LUX])

server = app.server

navigation_bar = html.Div(
    dbc.NavbarSimple([
        dbc.NavLink('About This App', href='/home', active='exact', id='home-navlink'),
        dbc.NavLink('Game Data', href='/game', active='exact', id='game-navlink'),
        dbc.NavLink("Lineup Data", href="/lineup", active="exact", id='lineup-navlink'
                    ),
        dbc.NavLink("Player Data", href="/players", active='exact', id='players-navlink'
                    ),
        ],
        color='primary',
        dark=True,
        brand= "Euroleague Advanced Statistics Dashboard"

    )
)

app.layout = html.Div([
    navigation_bar,
    dash.page_container])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=True)
