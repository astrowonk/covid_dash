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

# If I ever  deploy this I need to rysnc data_cache into this directory.
state_df = pd.read_csv("data_cache/us-states.csv")
county_df = pd.read_csv("data_cache/us-counties.csv")
county_df = county_df.drop("state", axis=1).rename({"state_county": "state"},
                                                   axis=1)
combined = pd.concat([
    county_df[["date", "state", "case_growth_per_100K"]],
    state_df[["date", "state", "case_growth_per_100K"]],
])
combined["date"] = pd.to_datetime(combined["date"])
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

markdown_text = """
### Covid Case Growth

This implements much of the functionality of my [Shiny app for covid case growth](/shiny/covid/) in [Dash/Flask](https://dash.plotly.com) for python.

Data is preprocessed/merged with census population data with R scripts twice a day. More details on data sources in the About section below. All Covid case data comes from the [New York Times](https://github.com/nytimes/covid-19-data)
"""

about_text = """So far, this Dash version performs and loads faster than Shiny, but the layout is still  simpler, and the Shiny site is 
actually Rmarkdown with a Shiny renderer. A normal Shiny app tends to perform better and would be better comparison. 
That said Dash [supports markdown](https://dash.plotly.com/dash-core-components/markdown), which I'm using to write all of this text.

Since I'm still getting a handle on the layout of dash apps, I have consolidated County and State data into one plot. 
You can pick either counties or entire states
from the multi-selection dropdown. Plots are always normalized per 100K population.

Covid Tracking and the New York Times have had at times very different total counts for some states, which can lead to very 
different case growth plots. Covid Tracking updates more frequently, but I am using the NYT as the default data source for state plots.

Covid Tracking includes a `positiveIncrease` column. For the NY Times data, this column is computed with a simple `mutate(case_growth = cases - lag(cases))` after sorting by date in an R script, prior to loading in this app.

I have looked for alternatives to county-level data from the [NY Times github](https://github.com/nytimes/covid-19-data). I haven't found any useful sources yet. It is unclear where the [John Hopkins](https://github.com/CSSEGISandData/COVID-19) county data comes from, and the data files that do exist there have a difficult to parse format, with the [values in different columns for different dates](https://github.com/CSSEGISandData/COVID-19/blob/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_US.csv)).

For state population I'm using POPESTIMATE19 from various CSV files available from the US Census. [US Census](https://www.census.gov/newsroom/press-kits/2019/national-state-estimates.html)

For county level I resolved UTF-8 issues (thanks BBedit!) with this [local data set with FIPS codes](https://github.com/prairie-guy/2019-State-and-County-Population-with-FIPS-key) and use that for merging.



"""

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
                              'width': '30%'
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


@app.callback(
    Output("line-chart", "figure"),
    [
        Input("states", "value"),
        Input("rolling_days", "value"),
    ],
)
def update_line_chart(states, rolling_days):
    dff = (combined.query("state in @states").sort_values(["date", "state"
                                                           ]).reset_index())
    # this rolling 7 day thing was truly tedious but I guess time + 7D makes more sense than just integer rolling.
    dff["rolling_case_growth_per_100K"] = (dff.groupby("state")[[
        "case_growth_per_100K", "date"
    ]].rolling(f"{rolling_days}D",
               on="date").mean().reset_index()["case_growth_per_100K"])
    fig = px.line(dff,
                  x="date",
                  y="rolling_case_growth_per_100K",
                  color="state")

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
                      yaxis_title="Case Growth Per 100K population",
                      autosize=True,
                      font=dict(size=10))
    fig.update_yaxes(automargin=True)
    fig.update_xaxes(automargin=True)
    return fig


if __name__ == "__main__":
    app.run_server(debug=True)
