# Covid-19 Per Capita New Case in Dash
[Dash](https://dash.plotly.com) app showing Covid new cases by state/county.

This app implements per-capita normalized plots of linear case growth of Covid-19, using data from the [New York Times](https://github.com/nytimes/covid-19-data). It is running [live on my personal web site](https://marcoshuerta.com/dash/covid/).

However it is running on a very small [Digital Ocean droplet](https://m.do.co/c/6e16d6da6cf4), so reducing memory usage has proven important.

The `download_and_merge.py` script checks for the most recent commit time of the data in the NY Times repository, then download and process the files. The repository is checked hourly. The state data file is relatively small, so it is processed with pandas and all the population data merged at once, before uploading to sqlite3 with sql alchemy.

The county data is much larger, and the merges more memory instensive, at least on relative to the memory on my virtual server, using `pandas`. I do some light processing on the raw csv file line by line in python, then use `sqlite3` command line utility to efficiently load the csv file into the sqlite database with `county_processing.sql`. This is much faster than pandas + sql alchemy, uses less memory, and less cpu. 

`sqlite3` then joins the county data and county population and stores a new enhanced table so no join is required at runtime. The `github` api is used to check the NY Time repository every hour, and only update the database if the files have been updated.



