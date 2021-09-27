For state population I'm using POPESTIMATE19 from various CSV files available from the [US Census](https://www.census.gov/newsroom/press-kits/2019/national-state-estimates.html). I would like to switch to 2020 census data, but for counties I need a data set organized by FIPS, which I have not found yet.

Some states (e.g. Florida) have stopped reporting new covid deaths by county.

For county level I resolved UTF-8 issues (thanks BBedit!) with this [local data set with FIPS codes](https://github.com/prairie-guy/2019-State-and-County-Population-with-FIPS-key) and use that for merging.

If more than 15 total states and counties are selected, only the first 15 will be displayed.

More information and source code is available at [my github repository](https://github.com/astrowonk/covid_dash).