# Covid-19 Per Capita New Case in Dash
[Dash](https://dash.plotly.com) app showing Covid new cases by state/county.

This app implements per-capita normalized plots of linear case growth of Covid-19, using data from the [New York Times](https://github.com/nytimes/covid-19-data).

The R scripts were not properly writing out the csv files that the dash app needs, so I have rewritten the downloaded and merge scripts with python/pandas in `download_and_merge.py`. The `download-and-merge-scripts` folder will probably be removed soon, as none of those used now. The [Shiny version](https://github.com/astrowonk/covid_shiny) of this app may be retired soon.

With the new python based functions, the needed data files are downloaded and merged twice a day via a cron job for the [Covid new cases dashboard running live at my web site](https://marcoshuerta.com/dash/covid/).
