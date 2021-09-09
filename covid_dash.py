import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
from sqlalchemy.engine import create_engine
from md_text import about_text, markdown_text

# state_df['date'] = pd.to_datetime(state_df['date'])
# I think this is here because the layout needs this list and I can't get it from  DataLoader?


class dataLoader:
    """Makes sure the data is the most recent, rather than statically load it once."""
    combined = None
    lastmt = None

    def __init__(self):

        self.dbc = create_engine('sqlite:///data_cache/covid_dash.db')

    def get_data(self, state_list):
        """get the data from the sql tables"""
        binding_string = ','.join(['?'] * len(state_list))
        # maybe I should have one table with an id row for state vs county
        data = pd.read_sql(
            f"select * from states where state in ({binding_string}) union all select * from counties where state in ({binding_string});",
            self.dbc,
            params=state_list * 2)

        data['date'] = pd.to_datetime(data['date'])
        return data.rename({'case_growth': 'New Cases'}, axis=1)

    def all_states(self):
        return sorted(
            list(
                pd.read_sql('select distinct state from states',
                            con=self.dbc)['state']))

    def all_counties(self):
        return sorted(
            list(
                pd.read_sql('select distinct state from counties',
                            con=self.dbc)['state']))


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
                         } for x in myDataLoader.all_states()],
                         value=["Virginia"],
                         multi=True,
                         persistence=True),
            html.Label("Choose Counties"),
            dcc.Dropdown(id="counties",
                         options=[{
                             "label": x,
                             "value": x
                         } for x in myDataLoader.all_counties()],
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
    dff = myDataLoader.get_data(states_and_counties).sort_values(
        ["date", "state"]).reset_index()
    # update : still dumb, transform is better than what I had before but why there isn't a clean handoff
    # between rolling groupby and transform I don't know
    dff["rolling_case_growth_per_100K"] = dff.groupby(
        'state')['case_growth_per_100K'].transform(
            lambda s: s.rolling(rolling_days, min_periods=1).mean())
    dff["rolling_new_cases"] = dff.groupby('state')['New Cases'].transform(
        lambda s: s.rolling(rolling_days, min_periods=1).mean())
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
