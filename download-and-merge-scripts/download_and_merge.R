source("functions.R")

state_data_nyt <- get_state_data_nyt()
state_data_covid_tracking <- get_state_data_covid_tracking()
county_data_nyt <- get_county_nyt()
county_pop <<- read_csv('2019_county_populations.csv')
county_data_nyt <- merge_county_pop(county_data_nyt,county_pop)

write_csv(county_data_nyt,"data_cache/us-counties.csv")
write_csv(state_data_nyt,"data_cache/us-states.csv")
write_csv(state_data_covid_tracking,"data_cache/daily_tracking.csv")
