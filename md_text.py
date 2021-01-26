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
different case growth plots. Covid Tracking updates more frequently, but I am using the NYT as the default data source for state plots. Covid Tracking includes a `positiveIncrease` column. For the NY Times data, this column is computed with a simple `mutate(case_growth = cases - lag(cases))` after sorting by date in an R script, prior to loading in this app.

Since I'm combining state and county level data, I've turned off the ability to switch between Covid Tracking and NY Times data for now.

I have looked for alternatives to county-level data from the [NY Times github](https://github.com/nytimes/covid-19-data). I haven't found any useful sources yet. It is unclear where the [John Hopkins](https://github.com/CSSEGISandData/COVID-19) county data comes from, and the data files that do exist there have a difficult to parse format, with the [values in different columns for different dates](https://github.com/CSSEGISandData/COVID-19/blob/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_US.csv)).

For state population I'm using POPESTIMATE19 from various CSV files available from the US Census. [US Census](https://www.census.gov/newsroom/press-kits/2019/national-state-estimates.html)

For county level I resolved UTF-8 issues (thanks BBedit!) with this [local data set with FIPS codes](https://github.com/prairie-guy/2019-State-and-County-Population-with-FIPS-key) and use that for merging.



"""