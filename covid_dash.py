from os import stat
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
from numpy.core.numeric import roll
import plotly.express as px
import pandas as pd
from md_text import about_text, markdown_text

# state_df['date'] = pd.to_datetime(state_df['date'])
# I think this is here because the layout needs this list and I can't get it from  DataLoader?


class dataLoader:
    """Makes sure the data is the most recent, rather than statically load it once."""
    combined = None
    lastmt = None

    def __init__(self):
        self.path = "data_cache/us-states.csv"

        self.reload_data()

    def reload_data(self):
        """checks mod times and loads the data"""
        if not self.lastmt or stat(self.path).st_mtime > self.lastmt:
            #we should probably import threading and just have a therad just call this method every 30 min rather than
            #the Interval stuff I'm doing.
            self.lastmt = stat(self.path).st_mtime
            state_df = pd.read_csv("data_cache/us-states.csv")

            self.all_states = sorted(list(state_df.state.unique()))
            county_df = pd.read_csv("data_cache/us-counties.csv")

            county_df = county_df.drop("state", axis=1,
                                       errors='ignore').rename(
                                           {"state_county": "state"}, axis=1)
            self.all_counties = sorted(
                list(county_df["state"].dropna().unique()))
            self.combined = pd.concat([
                county_df[[
                    "date", "state", "case_growth_per_100K", "case_growth"
                ]],
                state_df[[
                    "date", "state", "case_growth_per_100K", "case_growth"
                ]],
            ]).rename({'case_growth': 'New Cases'}, axis=1)

            self.combined["date"] = pd.to_datetime(self.combined["date"])

    @property
    def thedata(self):
        self.reload_data()
        return self.combined


myDataLoader = dataLoader()

app = dash.Dash("covid_dash",
                url_base_pathname="/dash/covid/",
                external_stylesheets=[dbc.themes.YETI],
                title="Covid Case Growth Plots",
                meta_tags=[
                    {
                        "name": "viewport",
                        "content": "width=device-width, initial-scale=1"
                    },
                ])
server = app.server
INTERVAL_MINUTES = 5
STYLE = {"marginBottom": 20, "marginTop": 20}

controls = dbc.Card(
    [
        dbc.FormGroup([
            html.Label("Choose States"),
            dcc.Dropdown(id="states",
                         options=[{
                             "label": x,
                             "value": x
                         } for x in myDataLoader.all_states],
                         value=["Virginia"],
                         multi=True,
                         persistence=True),
            html.Label("Choose Counties"),
            dcc.Dropdown(id="counties",
                         options=[{
                             "label": x,
                             "value": x
                         } for x in myDataLoader.all_counties],
                         value=[],
                         multi=True,
                         persistence=True)
        ]),
        dbc.FormGroup([
            html.Label("Rolling Average Days"),
            dcc.Slider(
                id="rolling_days",
                min=1,
                max=14,
                step=1,
                value=7,
                marks={x: f"{x}"
                       for x in range(15)},
            ),
            dcc.Interval(id='interval',
                         interval=1000 * 60 * INTERVAL_MINUTES,
                         n_intervals=0)
        ]),
    ],
    body=True,
)

main_tab_content = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(controls, md=4),
                dbc.Col(dcc.Graph(id="line-chart"), md=8),
            ],
            align="center",
        ),
    ],
    fluid=True,
    style=STYLE,
)

about_tab_content = dbc.Container([dcc.Markdown(about_text)],
                                  fluid=True,
                                  style=STYLE)

tabs = dbc.Tabs([
    dbc.Tab(main_tab_content, label="Graph"),
    dbc.Tab(about_tab_content, label="About"),
])

app.layout = dbc.Container([dcc.Markdown(markdown_text), tabs], style=STYLE)


@app.callback(
    Output("line-chart", "figure"),
    [
        Input("states", "value"),
        Input('counties', 'value'),
        Input("rolling_days", "value"),
        Input("interval", "n_intervals")
    ],
)
def update_line_chart(states, counties, rolling_days, n_intervals):
    states_and_counties = states + counties
    print(states_and_counties)
    dff = (myDataLoader.thedata.query(
        "state in @states_and_counties").sort_values(["date",
                                                      "state"]).reset_index())
    # this rolling 7 day thing was truly tedious but I guess time + 7D makes more sense than just integer rolling.
    dff["rolling_case_growth_per_100K"] = dff.groupby('state').rolling(
        f"{rolling_days}D",
        on="date")['case_growth_per_100K'].mean().reset_index().sort_values(
            ['date', 'state']).reset_index(drop=True)['case_growth_per_100K']
    dff["rolling_new_cases"] = dff.groupby('state').rolling(
        f"{rolling_days}D",
        on="date")['New Cases'].mean().reset_index().sort_values(
            ['date', 'state']).reset_index(drop=True)['New Cases']
    fig = px.line(dff,
                  x="date",
                  y="rolling_case_growth_per_100K",
                  color="state",
                  hover_data=[
                      'date', 'rolling_new_cases',
                      'rolling_case_growth_per_100K', 'New Cases',
                      'case_growth_per_100K'
                  ],
                  labels={'state': ''})

    fig.update_layout(margin={
        'l': 1,
        'r': 1,
        'b': 1,
        't': 10,
        'pad': 1,
    },
                      legend=dict(yanchor="top",
                                  y=0.99,
                                  xanchor="left",
                                  x=0.01),
                      xaxis_title=None,
                      yaxis_title="New Reported Cases Per 100,000",
                      autosize=True,
                      font=dict(size=12))
    fig.update_yaxes(automargin=True)
    fig.update_xaxes(automargin=True)

    return fig


if __name__ == "__main__":
    app.run_server(debug=True)
