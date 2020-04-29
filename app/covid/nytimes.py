"""
    Download COVID-19 data from NY Times
"""

from io import StringIO
from os import getcwd
from os.path import dirname, join

import pandas as pd
import requests

# pylint: disable=invalid-name

def download_nytimes():
    """
        Read NY Times data from github
    """

    # read data from url
    url_ct = 'https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-counties.csv'
    url_st = 'https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-states.csv'

    with requests.Session() as s:
        s.trust_env = False
        download = s.get(url_ct)
        html_counties = download.text
        download = s.get(url_st)
        html_states = download.text

    try:
        __file__
    except NameError:
        cwd = getcwd()
    else:
        cwd = dirname(__file__)

    # save it
    df = pd.read_csv(StringIO(html_counties))
    df.to_csv(join(cwd, 'data', 'us-counties.csv'), index=False)

    # save it
    df = pd.read_csv(StringIO(html_states))
    df.to_csv(join(cwd, 'data', 'us-states.csv'), index=False)


if __name__ == "__main__":

    # unit testing
    download_nytimes()
