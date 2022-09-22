from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
from md_text import about_text, markdown_text
from dataLoader import dataLoader
# state_df['date'] = pd.to_datetime(state_df['date'])
# I think this is here because the layout needs this list and I can't get it from  DataLoader?

import os
parent_dir = os.getcwd().split('/')[-1]

myDataLoader = dataLoader()

app = Dash("covid_dash",
                url_base_pathname=f"/dash/{parent_dir}/",
                external_stylesheets=[dbc.themes.YETI],
                title="Covid Case Growth Plots",
                meta_tags=[
                    {
                        "name": "viewport",
                        "content": "width=device-width, initial-scale=1"
                    },
                ])
server = app.server
STYLE = {"marginBottom": 30, "marginTop": 20}

controls = dbc.Card(
    [
        html.Div([
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
        html.Div([
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
        html.Div(children=[
            "Hover Data:",
            dbc.RadioItems(
                id='show_hover',
                options=[{
                    'label': x.title(),
                    'value': x
                } for x in [
                    'none',
                    'minimal',
                    'full',
                ]],
                persistence=True,
                value='minimal',
                inline=True,
            ),
            dbc.Checkbox(
                label="Show Spikeline",
                id='show_spike',
                persistence=True,
                value=False,
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
                dbc.Col(dbc.Spinner([
                    dcc.Graph(id="line-chart"),
                ],
                                    delay_hide=100,
                                    color='info'),
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
        Input("show_hover", "value"),
        Input("show_spike", "value"),
    ],
)
def update_line_chart(states, counties, rolling_days, data_type, show_hover,
                      show_spike):
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
        'b': 3,
        't': 10,
        'pad': 8,
    },
                      legend=dict(yanchor="top",
                                  y=0.99,
                                  xanchor="left",
                                  x=0.01),
                      xaxis_title=None,
                      yaxis_title=y_axis_label,
                      autosize=True,
                      font=dict(size=12),
                      hovermode='closest')
    if show_hover == 'minimal':
        fig.update_layout(hovermode="x")
        fig.update_traces(hovertemplate=None)
    elif show_hover == 'none':
        fig.update_traces(hovertemplate=None, hoverinfo='none')

    fig.update_yaxes(automargin=True,
                     showspikes=show_spike,
                     spikemode="across")
    fig.update_xaxes(automargin=True)

    return fig


if __name__ == "__main__":
    app.run_server(debug=True)
