import dash
import dash_core_components as dcc
from dash_core_components.Slider import Slider
import dash_html_components as html
from dash.dependencies import Input, Output
from numpy.core.numeric import roll
import plotly.express as px
import pandas as pd

# If I ever  deploy this I need to rysnc data_cache into this directory.
state_df = pd.read_csv("data_cache/us-states.csv")
county_df = pd.read_csv("data_cache/us-counties.csv")
county_df = county_df.drop('state', axis=1).rename({'state_county': 'state'},
                                                   axis=1)
combined = pd.concat([
    county_df[['date', 'state', 'case_growth_per_100K']],
    state_df[['date', 'state', 'case_growth_per_100K']]
])
combined['date'] = pd.to_datetime(combined['date'])
#state_df['date'] = pd.to_datetime(state_df['date'])
all_states = sorted(list(combined['state'].unique()))

app = dash.Dash('covid_dash', url_base_pathname='/dash_test/')
server = app.server
app.layout = html.Div(
    [
        html.H1("Covid Grow Plots"),
        html.Label('Choose State or County'),
        dcc.Dropdown(id='states',
                     options=[{
                         'label': x,
                         'value': x
                     } if ',' in x else {
                         'label': f'State of {x}',
                         'value': x
                     } for x in all_states],
                     value="Virginia",
                     multi=True),
        html.Label('Rolling Average Days'),
        dcc.Slider(id='rolling_days',
                   min=1,
                   max=14,
                   step=1,
                   value=7,
                   marks={x: f'{x}'
                          for x in range(15)}),
        dcc.Graph(id="line-chart"),
        #the slider is gigantic and I need to learn how to style this.
    ],
    style={
        'marginBottom': 50,
        'margin_top': 25
    })


@app.callback(Output("line-chart", "figure"),
              [Input("states", "value"),
               Input("rolling_days", "value")])
def update_line_chart(states, rolling_days):
    dff = combined.query("state in @states").sort_values(['date', 'state'
                                                          ]).reset_index()
    #this rolling 7 day thing was truly tedious but I guess time + 7D makes more sense than just integer rolling.
    dff['rolling_case_growth_per_100K'] = dff.groupby('state')[[
        'case_growth_per_100K', 'date'
    ]].rolling(f'{rolling_days}D',
               on='date').mean().reset_index()['case_growth_per_100K']
    fig = px.line(dff,
                  x="date",
                  y="rolling_case_growth_per_100K",
                  color='state')
    fig.update_layout(
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01))

    return fig


if __name__ == "__main__":
    app.run_server(debug=True)
