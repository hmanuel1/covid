"""
    Download COVID-19 data from NY Times
"""

from os.path import join
from io import StringIO

import pandas as pd
import requests

from utilities import cwd


def download_nytimes():
    """
        Read NY Times data from github
    """

    # read data from url
    url_ct = 'https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-counties.csv'
    url_st = 'https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-states.csv'

    with requests.Session() as session:
        session.trust_env = False
        download = session.get(url_ct)
        html_counties = download.text
        download = session.get(url_st)
        html_states = download.text

    # save it
    df = pd.read_csv(StringIO(html_counties))
    df.to_csv(join(cwd(), 'data', 'us-counties.csv'), index=False)

    # save it
    df = pd.read_csv(StringIO(html_states))
    df.to_csv(join(cwd(), 'data', 'us-states.csv'), index=False)


if __name__ == "__main__":

    # unit testing
    download_nytimes()
