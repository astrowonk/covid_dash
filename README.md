# Covid-19 Per Capita New Case in Dash
[Dash](https://dash.plotly.com) app showing Covid new cases by state/county.

This app implements per-capita normalized plots of linear case growth of Covid-19, using data from the [New York Times](https://github.com/nytimes/covid-19-data).

The R scripts were not properly writing out the csv files that the dash app needs (possibly encountering memory issues) so I have rewritten the downloaded and merge scripts with python/pandas in `download_and_merge.py`. 

The pandas merges to create the csv files were memory intensive, as was loading the entire county data set into memory. Recent updates have moved everything into a sqlite database. The county population is merged in via sql and only on a small subset of the data. This reduces the memory usage of the cron job that updates the data twice a day, and of the dash app itself.

Thus the [Covid new cases dashboard running live at my web site](https://marcoshuerta.com/dash/covid/) that runs this code uses less memory and I think has overall better performance.
