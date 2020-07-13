"""
    Download COVID-19 data from NY Times
"""

import numpy as np
import pandas as pd

from database import DataBase
from wrangler import (
    US_MAP_TABLE,
    STATE_MAP_TABLE
)
from sql import (
    COUNTIES_VIEW,
    DROP_COUNTIES_VIEW,
    STATES_VIEW,
    DROP_STATES_VIEW,
    US_MAP_PIVOT_VIEW,
    DROP_US_MAP_PIVOT_VIEW,
    CREATE_OPTIONS_TABLE,
    INSERT_USA_OPTION,
    DROP_OPTIONS_TABLE
)


# inputs
US_COUNTIES_TABLE = 'us_counties'
US_STATES_TABLE = 'us_states'

# outputs
NYTIMES_COUNTIES_TABLE = 'nytimes_counties'
NYTIMES_STATES_TABLE = 'nytimes_states'
LEVELS_TABLE = 'levels'
DATES_TABLE = 'dates'


# levels to map cases and deaths
# LEVELS = [0, 1, 10, 100, 250, 500, 5000, 10000, np.inf]
LEVELS = [0, 1, 500, 1000, 2500, 5000, 10000, 20000, np.inf]

URL_COUNTIES = 'https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-counties.csv'
URL_STATES = 'https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-states.csv'



def download_nytimes():
    """Read NY Times data from github
    """
    # read covid19 county by county data from url
    data = pd.read_csv(URL_COUNTIES, dtype={'fips': 'str'})

    _db = DataBase()
    _db.add_table(US_COUNTIES_TABLE, data, index=False)
    _db.close()

    # read covid19 state by state data from url
    data = pd.read_csv(URL_STATES, dtype={'fips': 'str'})

    _db = DataBase()
    _db.add_table(US_STATES_TABLE, data, index=False)
    _db.close()

    clean_counties_data()
    clean_states_data()
    add_metadata()


def clean_counties_data():
    """Clean US Counties data from NY Times

    Returns:
        DataFrame -- clean us counties data

    Updates:
        database table -- NYTIMES_COUNTIES_TABLEs
        database view -- COUNTIES_VIEW
    """
    _db = DataBase()
    data = _db.get_table(US_COUNTIES_TABLE, parse_dates=['date'])
    counties = _db.get_geotable(US_MAP_TABLE)
    states = _db.get_geotable(STATE_MAP_TABLE)
    _db.close()

    start = len(data)

    # use new york county fips for new york city
    data.loc[data['county'] == 'New York City', 'fips'] = '36061'

    # add state ids
    lookup = states.set_index('name')['state_id'].to_dict()
    data['state_id'] = data['state'].map(lookup)

    # add county ids - first attempt
    data['id'] = data['county'].str.lower() + data['state_id']
    counties['id'] = counties['name'].str.lower() + counties['state_id']
    lookup = counties[['id', 'county_id']].set_index('id')['county_id'].to_dict()
    data['county_id'] = data['id'].map(lookup)

    # add county ids - last attempt
    condition = (~data['fips'].isna()) & (data['county_id'].isna())
    data.loc[condition, 'county_id'] = data.loc[condition, 'fips']

    # get rid of data that is not in county meta data
    data = data[data['county_id'].isin(list(counties['county_id']))].copy(deep=True)

    # state ids base on county_ids
    lookup = counties.set_index('county_id')['state_id'].to_dict()
    data['state_id'] = data['county_id'].map(lookup)

    # days from lastest day
    delta_day = pd.to_timedelta(1, unit='days')
    data['day'] = (data['date'].max() - data['date']) / delta_day
    data['day'] = data['day'].astype('Int32')

    end = len(data)

    # ny times counties table
    cols = ['county_id', 'state_id', 'date', 'day', 'cases', 'deaths']
    data = data[cols].copy(deep=True)
    data.reset_index(drop=True, inplace=True)

    data['case_level'] = pd.cut(data['cases'], LEVELS, labels=range(1, len(LEVELS)))
    data['case_level'] = pd.to_numeric(data['case_level'], 'coerce').fillna(0)
    data['case_level'] = data['case_level'].astype('Int32')

    # ignored lines
    print(f'ignored lines: {start-end}/{start} = {(100*(start-end)/start):.01f}%')

    # tables to database
    _db = DataBase()
    _db.add_table(NYTIMES_COUNTIES_TABLE, data.set_index(['county_id', 'day']))
    _db.update(DROP_COUNTIES_VIEW)
    _db.update(COUNTIES_VIEW)
    _db.close()

    return data


def clean_states_data():
    """Clean US States data from NY Times

    Returns:
        DataFrame -- clean us states data

    Updates:
        database table -- NYTIMES_STATES_TABLEs
        database view -- STATES_VIEW
    """
    # covid19 data and metadata
    _db = DataBase()
    data = _db.get_table(US_STATES_TABLE, parse_dates=['date'])
    states = _db.get_geotable(STATE_MAP_TABLE)
    _db.close()

    start = len(data)

    # add state ids
    states['name'] = states['name'].str.lower()
    lookup = states.set_index('name')['state_id'].to_dict()
    data['state_id'] = data['state'].str.lower().map(lookup)

    # get rid of data that is not in county meta data
    data = data[data['state_id'].isin(list(states['state_id']))].copy(deep=True)

    # days from lastest reported date
    delta_day = pd.to_timedelta(1, unit='days')
    data['day'] = (data['date'].max() - data['date']) / delta_day
    data['day'] = data['day'].astype('Int32')

    end = len(data)

    # ny times table
    data = data[['state_id', 'date', 'day', 'cases', 'deaths']].copy(deep=True)
    data.reset_index(drop=True, inplace=True)

    # ignored lines
    print(f'ignored lines: {start-end}/{start} = {(100*(start-end)/start):.01f}%')

    # table to database
    _db = DataBase()
    _db.add_table(NYTIMES_STATES_TABLE, data.set_index('state_id'))
    _db.update(DROP_STATES_VIEW)
    _db.update(STATES_VIEW)
    _db.close()

    return data


def add_metadata():
    """Updates options, dates and levels database tables

    Updates:
        database table -- OPTIONS
        database table -- DATES
        database table -- LEVELS
    """
    _db = DataBase()
    _db.update(DROP_US_MAP_PIVOT_VIEW)
    _db.update(US_MAP_PIVOT_VIEW)
    data = _db.get_table(NYTIMES_COUNTIES_TABLE, parse_dates=['dates'])
    _db.close()

    data['date'] = pd.to_datetime(data['date'])

    # last 15 days
    dates = []
    latest_date = data['date'].max()
    for day in range(15):
        date = latest_date - pd.to_timedelta(day, 'days')
        dates.append(date)

    # meta data
    _db = DataBase()
    _db.add_table(LEVELS_TABLE, pd.DataFrame({'level': LEVELS}), index=False)
    _db.add_table(DATES_TABLE, pd.DataFrame({'date': dates}), index=False)
    _db.update(DROP_OPTIONS_TABLE)
    _db.update(CREATE_OPTIONS_TABLE)
    _db.update(INSERT_USA_OPTION)
    _db.close()


if __name__ == "__main__":

    # unit testing
    download_nytimes()
