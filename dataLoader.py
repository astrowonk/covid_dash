import pandas as pd
from sqlalchemy.engine import create_engine


class dataLoader:
    """Makes sure the data is the most recent, rather than statically load it once."""
    combined = None
    lastmt = None

    def __init__(self):

        self.dbc = create_engine('sqlite:///data_cache/covid_dash.db')

    def get_data(self, state_list, cases=True):
        """get the data from the sql tables"""
        # maybe I should have one table with an id row for state vs county
        county_list = [x for x in state_list if ',' in x]
        state_list = [x for x in state_list if ',' not in x]
        binding_string = ','.join(['?'] * len(state_list))
        if cases:
            data_states = pd.read_sql(
                f"select date, case_growth, state, case_growth_per_100K, cases from states where state in ({binding_string})",
                self.dbc,
                params=state_list)
        else:
            data_states = pd.read_sql(
                f"select date, new_deaths, state, new_deaths_per_100k, deaths from states where state in ({binding_string})",
                self.dbc,
                params=state_list)
        data_states['date'] = pd.to_datetime(data_states['date'])
        binding_string = ','.join(['?'] * len(county_list))
        if cases:
            data_counties = pd.read_sql(
                f'select c.date, c.state,c.cases, c.population from county_enhanced c where c.state in ({binding_string});',
                con=self.dbc,
                params=county_list)
            data_counties['date'] = pd.to_datetime(data_counties['date'])
            data_counties.sort_values('date', inplace=True)
            data_counties['case_growth'] = data_counties.groupby(
                ['state'])['cases'].shift(0) - data_counties.groupby(
                    ['state'])['cases'].shift(1)
            data_counties['case_growth_per_100K'] = 100000 * data_counties[
                'case_growth'] / data_counties['population']
        else:
            # handle data on deaths
            data_counties = pd.read_sql(
                f'select c.date, c.state,c.deaths, c.population from county_enhanced c where c.state in ({binding_string});',
                con=self.dbc,
                params=county_list)
            data_counties['date'] = pd.to_datetime(data_counties['date'])
            data_counties.sort_values('date', inplace=True)
            data_counties['new_deaths'] = data_counties.groupby(
                ['state'])['deaths'].shift(0) - data_counties.groupby(
                    ['state'])['deaths'].shift(1)
            data_counties['new_deaths_per_100K'] = 100000 * data_counties[
                'new_deaths'] / data_counties['population']
        data = pd.concat([data_states, data_counties])
        data['date'] = pd.to_datetime(data['date'])
        return data.rename(
            {
                'case_growth': 'New Cases',
                'new_deaths': 'New Deaths'
            }, axis=1)

    def all_states(self):
        return sorted(
            list(
                pd.read_sql('select distinct state from states',
                            con=self.dbc)['state']))

    def all_counties(self):
        return sorted(
            list(
                pd.read_sql('select distinct state from county_enhanced',
                            con=self.dbc)['state']))
