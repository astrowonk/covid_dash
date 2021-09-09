import pandas as pd
from sqlalchemy import create_engine, types, TEXT
import gc

dbc = create_engine('sqlite:///data_cache/covid_dash.db')
dytpe_dict = {
    'date': types.TEXT,
    'fips': types.TEXT,
    'case_growth': types.INTEGER,
    'state': types.TEXT,
}


def get_county_data():
    the_county_data = pd.read_csv(
        'https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-counties.csv'
    )

    the_county_data['date'] = pd.to_datetime(the_county_data['date'])
    the_county_data.sort_values('date', inplace=True)
    # the_county_data['case_growth'] = the_county_data.groupby(
    #     ['county', 'state'])['cases'].shift(0) - the_county_data.groupby(
    #         ['county', 'state'])['cases'].shift(1)
    return the_county_data


def merge_county_pop(county_data, pop_data):
    county_data[
        'state_county'] = county_data['county'] + ', ' + county_data['state']
    res = county_data[['date', 'fips', 'case_growth',
                       'state_county']].merge(pop_data[['fips', 'population']],
                                              on=['fips'],
                                              how='left')
    res['case_growth_per_100K'] = 100000 * res['case_growth'] / res[
        'population']
    return res.rename(columns={
        'state_county': 'state'
    }).drop(columns=['population', 'fips'], errors='ignore')


def get_state_nyt(pop_data):
    state_nyt = pd.read_csv(
        'https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-states.csv'
    ).drop(columns=['deaths', 'fips'])
    state_nyt['date'] = pd.to_datetime(state_nyt['date'])
    state_nyt.sort_values('date', inplace=True)
    state_nyt['case_growth'] = state_nyt.groupby([
        'state'
    ])['cases'].shift(0) - state_nyt.groupby(['state'])['cases'].shift(1)
    state_nyt = state_nyt[['date', 'case_growth', 'state'
                           ]].merge(pop_data[['POPESTIMATE2019', 'NAME']],
                                    left_on='state',
                                    right_on='NAME',
                                    how='left')
    #   state_nyt['cases_per_100K'] = 100000 * state_nyt['cases'] / state_nyt[
    #       'POPESTIMATE2019']
    state_nyt['case_growth_per_100K'] = 100000 * state_nyt[
        'case_growth'] / state_nyt['POPESTIMATE2019']

    return state_nyt.sort_values('date').drop(
        columns=['NAME', 'name', 'POPESTIMATE2019'], errors='ignore')


def write_county_sql():
    pop_data_county = pd.read_csv('2019_county_populations.csv')
    dytpe_dict = {
        'date': types.TEXT,
        'fips': types.TEXT,
        'cases': types.INTEGER,
        'state': types.TEXT,
    }
    pop_data_county.to_sql('county_population',
                           dbc,
                           if_exists='replace',
                           dtype=dytpe_dict)
    with dbc.connect() as con:
        _ = con.execute('create index idx_fips on county_population (fips);')


def upload_state_to_sql():
    pop_data_state = pd.read_csv('SCPRC-EST2019-18+POP-RES.csv')
    state_nyt = get_state_nyt(pop_data=pop_data_state)
    state_nyt['date'] = state_nyt['date'].apply(
        lambda x: x.strftime('%Y-%m-%d'))
    state_nyt.to_sql('states',
                     dbc,
                     if_exists='replace',
                     dtype=dytpe_dict,
                     index=False,
                     chunksize=10000,
                     method='multi')


def upload_county_to_sql():
    print('loading county data')
    county_data = get_county_data()

    print('perfoming operations on county dataframe')
    county_data['date'] = county_data['date'].apply(
        lambda x: x.strftime('%Y-%m-%d'))
    county_data['state'] = county_data['county'] + ', ' + county_data['state']

    print("Writing to sql counties")
    county_data.to_sql('counties',
                       dbc,
                       if_exists='replace',
                       dtype=dytpe_dict,
                       index=False,
                       chunksize=5000,
                       method='multi')


if __name__ == '__main__':

    print("Writing to sql states")
    upload_state_to_sql()
    gc.collect()
    print("Creating SQL indexes")
    upload_county_to_sql()
    gc.collect()
    with dbc.connect() as con:
        _ = con.execute('create index idx_state on counties (state);')
        #     _ = con.execute('create index idx_state on counties (fips);')
        _ = con.execute('create index idx_county on states (state);')