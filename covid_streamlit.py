import streamlit as st
import plotly.express as px

from dataLoader import dataLoader
myDataLoader = dataLoader()

st.set_page_config(page_title="Covid Case Growth Plots", layout='wide')

st.title('Covid Case Growth Plots')
## layout
with st.sidebar:
    states = st.multiselect('State:', myDataLoader.all_states(), ['Virginia'])
    counties = st.multiselect('Counties:', myDataLoader.all_counties(),
                              ['Henrico, Virginia'])
    data_type = st.selectbox('Data Type:', ['Cases', 'Deaths'])
    rolling_days = st.slider('Rolling Average Days:', 1, 14, 7)
    show_hover = st.radio('Show Hover Data:', ['none', 'minimal', 'full'], 2)
    show_spike = st.checkbox('Show Spikeline:', False)

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

states_and_counties = states + counties

if len(states_and_counties) > 15:
    #quietly limiting the length of the list to 15
    states_and_counties = states_and_counties[:15]
dff = myDataLoader.get_data(states_and_counties,
                            cases=cases).sort_values(["date",
                                                      "state"]).reset_index()

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
                  legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
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
fig.update_yaxes(
    automargin=True,
    showspikes=show_spike,
    spikemode="across",
)
fig.update_xaxes(automargin=True)

st.plotly_chart(fig, use_container_width=False)
