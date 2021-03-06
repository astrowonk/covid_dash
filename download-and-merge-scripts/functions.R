require(readr)
require(dplyr)
require(magrittr)
require(jsonlite)





get_county_nyt <- function () {
    
    county_data <-  read_csv(url("https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-counties.csv"))
    county_data$date <- as.Date(county_data$date)
    county_data <- county_data[order(county_data$date),]
    county_data <- county_data %>% group_by(county,state) %>% mutate(case_growth = cases - lag(cases))
    return(county_data)
}




merge_county_pop <- function (county_data,pop_data) {
    county_data <-
        merge(
            county_data,
            select(pop_data,fips,population),
            by = 'fips',
            all.x = TRUE
        )
    county_data <-
        mutate(
            county_data,
            cases_per_100K = 100000 * (cases / population),
            case_growth_per_100K = 100000 * (case_growth / population)
        )
    county_data <- mutate(county_data,state_county = paste(county,state,sep=", "))
    return(county_data)
    
}


get_state_data_nyt <- function() {
    state_data <-
        read_csv(
            url(
                "https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-states.csv"
            )
        )
    state_data$date <- state_data$date %>% as.Date()
    state_data <- state_data[order(state_data$date), ]
    state_data <- state_data %>%
        group_by(state) %>%
        mutate(case_growth = cases - lag(cases))
   pop_data <- read_csv('SCPRC-EST2019-18+POP-RES.csv')
   state_data <-
       merge(
           state_data,
           pop_data,
           by.x = 'state',
           by.y = 'NAME',
           all.x = TRUE
       )
   state_data <-
       mutate(
           state_data,
           cases_per_100K = 100000 * (cases / POPESTIMATE2019),
           case_growth_per_100K = 100000 * (case_growth / POPESTIMATE2019)
       )
    state_data <- state_data[order(state_data$date), ]
    return(state_data)
}

get_state_data_covid_tracking <- function() {
    state_json <-
        fromJSON(txt = url("https://covidtracking.com/api/states/daily"))
    state_json$date <- as.Date(state_json$dateChecked)
    state_json <- state_json %>% rename(state_abbr = state)
    state_info <-
        read_csv("state_info.csv") %>% select(state_abbr = state, state = name)
    state_json <-
        merge(state_json, state_info, by = "state_abbr", all.x = TRUE) %>% rename(case_growth = positiveIncrease, cases =
                                                                                      positive)
    #merge population data, create new columns
    pop_data <- read_csv('SCPRC-EST2019-18+POP-RES.csv')
    state_json <-
        merge(
            state_json,
            pop_data,
            by.x = 'state',
            by.y = 'NAME',
            all.x = TRUE
        )
    state_json <-
        mutate(
            state_json,
            cases_per_100K = 100000 * (cases / POPESTIMATE2019),
            case_growth_per_100K = 100000 * (case_growth / POPESTIMATE2019)
        )
    state_json <- state_json[order(state_json$date), ]
    
    return(state_json)
}

