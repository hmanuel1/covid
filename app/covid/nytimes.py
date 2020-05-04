"""
    Download COVID-19 data from NY Times
"""

from os.path import join

import pandas as pd

from utilities import cwd


def download_nytimes():
    """
        Read NY Times data from github
    """

    # read data from url
    url_ct = 'https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-counties.csv'
    url_st = 'https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-states.csv'

    # save it
    df = pd.read_csv(url_ct)
    df.to_csv(join(cwd(), 'data', 'us-counties.csv'), index=False)

    # save it
    df = pd.read_csv(url_st)
    df.to_csv(join(cwd(), 'data', 'us-states.csv'), index=False)


if __name__ == "__main__":

    # unit testing
    download_nytimes()
