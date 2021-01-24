import dash
import dash_core_components as dcc
from dash_core_components.Slider import Slider
import dash_html_components as html
import dash_bootstrap_components as dbc
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

app = dash.Dash('covid_dash', url_base_pathname='/dash/covid/')
server = app.server

markdown_text = '''
### Dash Implementation of Covid Case Growth Tracker.

This implements some of the functionality of my [Shiny app for covid case growth](/shiny/covid/).
It performs and loads faster than Shiny, but the layout is so far much simpler, and the Shiny site is 
actually Rmarkdown with a Shiny renderer. Presumably a straight Shiny app would be better comparison. 

Since I'm still getting a handle on the layout of dash apps, I have consolidated County and State data into one plot. You can pick either counties or entire states
from the multi-selection dropdown. Plots are always normalized per 100K population.

Data has been preprocessed/merged with census population data before loading into this app. More details on data sources in the About section of the 
Shiny link above. All Covid case data comes from the [New York Times](https://github.com/nytimes/covid-19-data)

'''

app.layout = html.Div(
    [
        html.H1("Covid Grow Plots"),
        dcc.Markdown(markdown_text),
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
    fig.update_layout(legend=dict(yanchor="top",
                                  y=0.99,
                                  xanchor="left",
                                  x=0.01),
                      xaxis_title="Date",
                      yaxis_title="Case Growth Per 100K population")

    return fig


if __name__ == "__main__":
    app.run_server(debug=True)
