# Covid-19 Per Capita New Case in Dash
Dash implementation of Covid case plot.

This app implements per-capita normalized plots of case growth of Covid-19, using data from the [New York Times](https://github.com/nytimes/covid-19-data).

My original app was written in Shiny, so most of the code that downloads and merges is still written in R. I have included these scripts, though I think I got the dependencies right, they actually run daily from another repo. I should probably rewrite these with pandas at some point.

This code is currently running live at [my web site](https://marcoshuerta.com/dash/covid/)
