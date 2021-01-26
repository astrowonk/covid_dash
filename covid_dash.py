from os import stat
import dash
import dash_core_components as dcc
from dash_core_components.Slider import Slider
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
from numpy.core.numeric import roll
import plotly.express as px
import pandas as pd
from md_text import about_text, markdown_text

# If I ever  deploy this I need to rysnc data_cache into this directory.

state_df = pd.read_csv("data_cache/us-states.csv")
county_df = pd.read_csv("data_cache/us-counties.csv")
county_df = county_df.drop("state", axis=1).rename({"state_county": "state"},
                                                   axis=1)
combined = pd.concat([
    county_df[["state"]],
    state_df[["state"]],
])
# state_df['date'] = pd.to_datetime(state_df['date'])
all_states = sorted(list(combined["state"].unique()))

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
            dcc.Checklist(id='state_county_checklist',
                          options=[{
                              'label': x,
                              'value': x
                          } for x in ["States", "Counties"]],
                          value=["States", "Counties"],
                          inputStyle={
                              "margin-left": "5px",
                              "margin-right": "5px",
                              "padding-right": "5px"
                          },
                          style={
                              'display': 'block',
                              'width': '25%'
                          }),
            html.Label("Choose State or County"),
            dcc.Dropdown(
                id="states",
                options=[{
                    "label": x,
                    "value": x
                } if "," in x else {
                    "label": f"State of {x}",
                    "value": x
                } for x in all_states],
                value="Virginia",
                multi=True,
            ),
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
            dcc.Interval(id='interval', interval=5000, n_intervals=0)
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


@app.callback(Output("states", "options"),
              [Input("state_county_checklist", "value")])
def update_dropdown(state_county_check_list):
    if len(state_county_check_list) == 2:
        return [{
            "label": x,
            "value": x
        } if "," in x else {
            "label": f"State of {x}",
            "value": x
        } for x in all_states]
    elif "States" in state_county_check_list:
        return [{"label": x, "value": x} for x in all_states if "," not in x]
    return [{"label": x, "value": x} for x in all_states if "," in x]


class dataLoader:
    combined = None
    lastmt = None

    def __init__(self):
        pass
        self.path = "data_cache/us-states.csv"
        self.reload_data()

    def reload_data(self):
        if not self.lastmt or stat(self.path).st_mtime > self.lastmt:
            self.lastmt = stat(self.path).st_mtime
            state_df = pd.read_csv("data_cache/us-states.csv")
            county_df = pd.read_csv("data_cache/us-counties.csv")
            county_df = county_df.drop("state", axis=1).rename(
                {"state_county": "state"}, axis=1)
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


@app.callback(
    Output("line-chart", "figure"),
    [
        Input("states", "value"),
        Input("rolling_days", "value"),
        Input("interval", "n_intervals")
    ],
)
def update_line_chart(states, rolling_days, n_intervals):

    dff = (myDataLoader.thedata.query("state in @states").sort_values(
        ["date", "state"]).reset_index())
    # this rolling 7 day thing was truly tedious but I guess time + 7D makes more sense than just integer rolling.
    dff["rolling_case_growth_per_100K"] = (dff.groupby("state")[[
        "case_growth_per_100K", "date"
    ]].rolling(f"{rolling_days}D",
               on="date").mean().reset_index()["case_growth_per_100K"])
    dff["rolling_new_cases"] = (dff.groupby("state")[[
        "New Cases", "date"
    ]].rolling(f"{rolling_days}D",
               on="date").mean().reset_index()["New Cases"])
    fig = px.line(dff,
                  x="date",
                  y="rolling_case_growth_per_100K",
                  color="state",
                  hover_data=[
                      'date', 'rolling_new_cases',
                      'rolling_case_growth_per_100K', 'New Cases',
                      'case_growth_per_100K'
                  ])

    fig.update_layout(margin={
        'l': 1,
        'r': 1,
        'b': 1,
        't': 10,
        'pad': 1
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
