markdown_text = """
### Covid Case Growth

Plots are normalized per 100K population. Data is preprocessed/merged with census population data with R scripts twice a day. More details on data sources in the About section below. 

All Covid case data comes from the [New York Times](https://www.nytimes.com/interactive/2020/us/coronavirus-us-cases.html), which hosts the data on [their github repository](https://github.com/nytimes/covid-19-data).

Code is all available on [github](https://github.com/astrowonk/covid_dash).

"""

about_text = """I'm not aware of any other site where one can see normalized case growth across counties and states on the same graph. I hope you find it useful.

I have looked for alternatives to county-level data from the [NY Times github](https://github.com/nytimes/covid-19-data). I haven't found any useful sources yet. It is unclear where the [John Hopkins](https://github.com/CSSEGISandData/COVID-19) county data comes from, and the data files that do exist there have a difficult to parse format, with the [values in different columns for different dates](https://github.com/CSSEGISandData/COVID-19/blob/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_US.csv)).

For state population I'm using POPESTIMATE19 from various CSV files available from the [US Census](https://www.census.gov/newsroom/press-kits/2019/national-state-estimates.html)

For county level I resolved UTF-8 issues (thanks BBedit!) with this [local data set with FIPS codes](https://github.com/prairie-guy/2019-State-and-County-Population-with-FIPS-key) and use that for merging.




"""