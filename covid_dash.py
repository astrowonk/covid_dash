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

    def get_data(self, state_list, cases=True):
        """get the data from the sql tables"""
        # maybe I should have one table with an id row for state vs county
        county_list = [x for x in state_list if ',' in x]
        state_list = [x for x in state_list if ',' not in x]
        binding_string = ','.join(['?'] * len(state_list))
        if cases:
            data_states = pd.read_sql(
                f"select date, case_growth, state, case_growth_per_100K, cases from states where state in ({binding_string})",
                self.dbc,
                params=state_list)
        else:
            data_states = pd.read_sql(
                f"select date, new_deaths, state, new_deaths_per_100k, deaths from states where state in ({binding_string})",
                self.dbc,
                params=state_list)
        data_states['date'] = pd.to_datetime(data_states['date'])
        binding_string = ','.join(['?'] * len(county_list))
        if cases:
            data_counties = pd.read_sql(
                f"select state,cases, date from counties where c.state in ({binding_string})"
            ).merge(pd.read_sql(), on='fips', how='left')
            data_counties = pd.read_sql(
                f'select c.date, c.state,c.cases, p.population from counties c left join county_population p on c.fips = p.fips where c.state in ({binding_string});',
                con=self.dbc,
                params=county_list)
            data_counties['date'] = pd.to_datetime(data_counties['date'])
            data_counties.sort_values('date', inplace=True)
            data_counties['case_growth'] = data_counties.groupby(
                ['state'])['cases'].shift(0) - data_counties.groupby(
                    ['state'])['cases'].shift(1)
            data_counties['case_growth_per_100K'] = 100000 * data_counties[
                'case_growth'] / data_counties['population']
        else:
            # handle data on deaths
            data_counties = pd.read_sql(
                f'select c.date, c.state,c.deaths, p.population from counties c left join county_population p on c.fips = p.fips where c.state in ({binding_string});',
                con=self.dbc,
                params=county_list)
            data_counties['date'] = pd.to_datetime(data_counties['date'])
            data_counties.sort_values('date', inplace=True)
            data_counties['new_deaths'] = data_counties.groupby(
                ['state'])['deaths'].shift(0) - data_counties.groupby(
                    ['state'])['deaths'].shift(1)
            data_counties['new_deaths_per_100K'] = 100000 * data_counties[
                'new_deaths'] / data_counties['population']
        data = pd.concat([data_states, data_counties])
        data['date'] = pd.to_datetime(data['date'])
        return data.rename(
            {
                'case_growth': 'New Cases',
                'new_deaths': 'New Deaths'
            }, axis=1)

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
STYLE = {"marginBottom": 20, "marginTop": 20}

controls = dbc.Card(
    [
        dbc.FormGroup([
            html.Label("Choose Data Type"),
            dcc.Dropdown(id='data-type',
                         options=[{
                             'label': x,
                             'value': x
                         } for x in ['Cases', 'Deaths']],
                         value='Cases',
                         persistence=True,
                         clearable=False),
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
            )
        ]),
    ],
    body=True,
)

main_tab_content = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(controls, md=4),
                dbc.Col(dbc.Spinner(
                    [
                        dcc.Graph(id="line-chart"),
                    ], debounce=100, color='info'),
                        md=8),
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
        Input("data-type", "value"),
    ],
)
def update_line_chart(states, counties, rolling_days, data_type,
                      existing_figure):
    states_and_counties = states + counties
    if data_type == 'Cases':
        y_axis_label = "New Reported Cases Per 100,000"
        y_variable = 'rolling_case_growth_per_100K'
        hover_data = [
            'date', 'rolling_new_cases', 'rolling_case_growth_per_100K',
            'New Cases', 'case_growth_per_100K'
        ]
        cases = True
    else:
        y_axis_label = "New Reported Deaths Per 100,000"
        y_variable = 'rolling_new_deaths_per_100K'
        hover_data = [
            'date', 'rolling_new_deaths_per_100K', 'new_deaths_per_100K'
        ]
        cases = False

    if len(states_and_counties) > 15:
        #quietly limiting the length of the list to 15
        states_and_counties = states_and_counties[:15]
    dff = myDataLoader.get_data(states_and_counties,
                                cases=cases).sort_values(["date", "state"
                                                          ]).reset_index()
    # update : still dumb, transform is better than what I had before but why there isn't a clean handoff
    # between rolling groupby and transform I don't know
    if cases:
        dff["rolling_case_growth_per_100K"] = dff.groupby(
            'state')['case_growth_per_100K'].transform(
                lambda s: s.rolling(rolling_days, min_periods=1).mean())
        dff["rolling_new_cases"] = dff.groupby('state')['New Cases'].transform(
            lambda s: s.rolling(rolling_days, min_periods=1).mean())
    else:

        dff["rolling_new_deaths_per_100K"] = dff.groupby(
            'state')['new_deaths_per_100K'].transform(
                lambda s: s.rolling(rolling_days, min_periods=1).mean())
    fig = px.line(dff,
                  x="date",
                  y=y_variable,
                  color="state",
                  hover_data=hover_data,
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
                      yaxis_title=y_axis_label,
                      autosize=True,
                      font=dict(size=12))
    fig.update_yaxes(automargin=True)
    fig.update_xaxes(automargin=True)

    return fig


if __name__ == "__main__":
    app.run_server(debug=True)
