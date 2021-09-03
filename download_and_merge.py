import pandas as pd


def get_county_data():
    county_data = pd.read_csv(
        'https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-counties.csv'
    )

    county_data['date'] = pd.to_datetime(county_data['date'])
    county_data.sort_values('date', inplace=True)
    county_data['case_growth'] = county_data.groupby(
        ['county', 'state'])['cases'].shift(0) - county_data.groupby(
            ['county', 'state'])['cases'].shift(1)
    return county_data


def merge_county_pop(county_data, pop_data):
    res = county_data.merge(pop_data[['fips', 'population']],
                            on=['fips'],
                            how='left')
    res['cases_per_100K'] = 100000 * res['cases'] / res['population']
    res['case_growth_per_100K'] = 100000 * res['case_growth'] / res[
        'population']
    res['state_county'] = res['county'] + ', ' + res['state']
    return res


def get_state_nyt(pop_data):
    state_nyt = pd.read_csv(
        'https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-states.csv'
    )
    state_nyt['date'] = pd.to_datetime(state_nyt['date'])
    state_nyt.sort_values('date', inplace=True)
    state_nyt['case_growth'] = state_nyt.groupby([
        'state'
    ])['cases'].shift(0) - state_nyt.groupby(['state'])['cases'].shift(1)
    state_nyt = state_nyt.merge(pop_data[['POPESTIMATE2019', 'NAME']],
                                left_on='state',
                                right_on='NAME',
                                how='left')
    state_nyt['cases_per_100K'] = 100000 * state_nyt['cases'] / state_nyt[
        'POPESTIMATE2019']
    state_nyt['case_growth_per_100K'] = 100000 * state_nyt[
        'case_growth'] / state_nyt['POPESTIMATE2019']

    return state_nyt.sort_values('date')


if __name__ == '__main__':
    county_data = get_county_data()
    pop_data_state = pd.read_csv('SCPRC-EST2019-18+POP-RES.csv')
    state_nyt = get_state_nyt(pop_data=pop_data_state)
    pop_data_county = pd.read_csv('2019_county_populations.csv')
    county_data = merge_county_pop(county_data, pop_data_county)
    county_data.to_csv('data_cache/us-counties.csv', index=False)
    state_nyt.to_csv('data_cache/us-states.csv', index=False)
