import pandas as pd
from sqlalchemy import create_engine, types, TEXT
import gc
from tqdm import tqdm
import csv
from urllib.request import urlretrieve
from github import Github
from datetime import datetime
from os.path import getmtime
import subprocess

dbc = create_engine('sqlite:///data_cache/covid_dash.db')
dytpe_dict = {
    'date': types.TEXT,
    'fips': types.TEXT,
    'case_growth': types.INTEGER,
    'state': types.TEXT,
}


def check_for_new_download():
    """Check if github mod time is later than downloaded file modtime and return True if it needs to be dowloaded again."""
    gh = Github()
    repo = gh.get_repo('nytimes/covid-19-data')
    commits = repo.get_commits(path='us-counties.csv')
    gh_mod_time = commits[0].commit.committer.date
    file_mod_time = datetime.fromtimestamp(
        getmtime('data_cache/covid_dash.db'))
    print(
        f"Github Last commit {gh_mod_time}, Database mod time {file_mod_time}")
    return gh_mod_time > file_mod_time


def load_and_rewrite_county_csv():
    """Memory saving line by line csv load and concatenate county and state"""
    print("Writing new csv file")
    urlretrieve(
        'https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-counties.csv',
        filename='data_cache/us-counties.csv')

    with open('data_cache/temp.csv', 'w', newline='') as csvfile:
        fieldnames = ['date', 'state', 'fips', 'cases', 'deaths']
        mywriter = csv.writer(csvfile,
                              delimiter=',',
                              quotechar='"',
                              quoting=csv.QUOTE_MINIMAL)
        mywriter.writerow(fieldnames)

        with open('data_cache/us-counties.csv') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            header = next(reader)
            print(header)
            for row in tqdm(reader):

                new_entry = [row[1] + ', ' + row[2]]
                new_row = row[:1] + new_entry + row[3:]
                mywriter.writerow(new_row)


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
    """Considerably smaller data file so merging and pre-computing some data before uploading to sqlite db is practical"""
    state_nyt = pd.read_csv(
        'https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-states.csv'
    ).drop(columns=['fips'])
    state_nyt['date'] = pd.to_datetime(state_nyt['date'])
    state_nyt.sort_values('date', inplace=True)
    state_nyt['case_growth'] = state_nyt.groupby([
        'state'
    ])['cases'].shift(0) - state_nyt.groupby(['state'])['cases'].shift(1)
    state_nyt['new_deaths'] = state_nyt.groupby([
        'state'
    ])['deaths'].shift(0) - state_nyt.groupby(['state'])['deaths'].shift(1)
    state_nyt = state_nyt[['date', 'case_growth', 'state', 'new_deaths'
                           ]].merge(pop_data[['POPESTIMATE2019', 'NAME']],
                                    left_on='state',
                                    right_on='NAME',
                                    how='left')

    state_nyt['case_growth_per_100K'] = 100000 * state_nyt[
        'case_growth'] / state_nyt['POPESTIMATE2019']
    state_nyt['new_deaths_per_100K'] = 100000 * state_nyt[
        'new_deaths'] / state_nyt['POPESTIMATE2019']

    return state_nyt.sort_values('date').drop(
        columns=['NAME', 'name', 'POPESTIMATE2019'], errors='ignore')


def upload_state_to_sql():
    """Load state data and upload to sql"""
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


if __name__ == '__main__':

    if check_for_new_download():
        print("Writing to sql states")

        upload_state_to_sql()

        load_and_rewrite_county_csv()

        gc.collect()
        with dbc.connect() as con:
            print("Making State Indexes")
            _ = con.execute('create index idx_county on states (state);')

        print('running .sql script to read temp csv')
        subprocess.run([
            'sqlite3', 'data_cache/covid_dash.db',
            '.read county_processing.sql'
        ])
    else:
        print("No new data in github to process")
