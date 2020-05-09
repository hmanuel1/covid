"""
    Read pdf COVID-19 file from Florida Division of Emergency
    Management and save it into a CSV format
"""

from io import BytesIO
import re

import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
import PyPDF2

from database import DataBase
from wrangler import US_MAP_TABLE
from sql import (
    DROP_FLDEM_VIEW,
    FLDEM_VIEW
)


# inputs
FL_CASES_TABLE = 'fl_cases'
FL_DEATHS_TABLE = 'fl_deaths'

# outputs
FLDEM_CASES_TABLE = 'fldem_cases'
FLDEM_DEATHS_TABLE = 'fldem_deaths'


class PdfScraper:
    """This class read a pdf file from an url and transform text
        into a pandas dataframe.
    """

    # data urls
    BASE_URL = 'https://floridadisaster.org'
    COVID19_URL = 'https://floridadisaster.org/covid19/'

    def __init__(self):
        self.url = None
        self.pages = None
        self.lines = None
        self.data = None

        # get pdf file url
        self.__get_url()

    def __get_url(self):
        """Extract pdf file url

        Arguments:
            url {String} -- url to extract pdf file url
        """
        # get html
        _response = requests.get(self.COVID19_URL)
        _html = _response.text
        _soup = BeautifulSoup(_html, features='html.parser')
        _body = _soup.find('div', {'class': 'panel-body'})
        _paragraphs = _body.find_all('p')

        _data = []
        for _paragraph in _paragraphs:
            _sentences = _paragraph.find_all('a')
            _data.append(str(_sentences[0]))

        _line = [x for x in _data if re.search(r'Daily Report', x)][0]

        # find sub url of pdf file
        _match = re.search(r'\"(.+?)\"', _line)
        if _match:
            self.url = self.BASE_URL + _match.group(1)
        else:
            self.url = 'NA'

    def get_pages(self):
        """Extract text pages from pdf file
        """
        # read pdf file from url
        _response = requests.get(self.url)
        _pdffile = _response.content

        # read pdf content
        _reader = PyPDF2.PdfFileReader(BytesIO(_pdffile))

        # extract text from each pdf page
        self.pages = []
        for _page in range(_reader.numPages):
            self.pages.append(_reader.getPage(_page).extractText())

    def __get_lines(self, marker):
        """Extract text lines from pdf pages

        Arguments:
            marker {String} -- identifier of data in text
        """
        # remove non-data pages
        _pages = [page for page in self.pages if re.search(marker, page[:100])]

        # unwanted lines contains these words
        _regex = re.compile(('Data|Death|County|Age|Gender|Travel|related|'
                             'Contact|confirmed|Jurisdiction|Date|counted|'
                             'today|Coronavirus|case|verified|Deaths'), re.IGNORECASE)

        _pages = [page.split('\n') for page in _pages]
        self.lines = [line for page in _pages for line in page
                      if not re.search(_regex, line)]

    def get_data(self, marker):
        """Extract data from pdf text

        Arguments:
            marker {String} -- identifier of data in text

        Returns:
            DataFrame -- data extracted from pdf
        """
        # get pages that contain specified <marker>
        self.__get_lines(marker)

        # tag start of row by date
        _tags = [(x, 'e') if re.search(r'\d{2}\/', x) else (x, 'b')
                 for x in self.lines]

        # rows
        _rows = []
        _cells = []
        for _cell in _tags:
            if _cell[1] == 'b':
                _cells.append(_cell[0])
            else:
                _cells.append(_cell[0])
                _rows.append(_cells)
                _cells = []

        #  fill missing data
        for _row in _rows:
            if not _row[0].replace(',', '').isnumeric():
                del _row[0]
            if not _row[1]:
                _row[1] = 'Unknown'
            if len(_row) == 7:
                _row.insert(4, 'Unknown')
            if len(_row) == 8:
                _row.insert(5, 'NaN')
            if len(_row) == 10:
                _row[5] = _row[5].join(_row[6])
                del _row[6]

        # create dataframe with extracted data
        _rows = [_row for _row in _rows if len(_row) == 9]
        _cols = ['case', 'county', 'age', 'gender', 'traveled', 'place',
                 'contacted', 'resident', 'date']

        # enter data in data frame and format
        self.data = pd.DataFrame(_rows, columns=_cols)
        self.data['age'] = pd.to_numeric(self.data['age'], errors='coerce')

        return self.data


def get_data(download=False):
    """Download data from web or from file

    Keyword Arguments:
        download {bool} -- get data from source (default: {False})

    Returns:
        DataFrame -- florida covid19 cases and deaths data
    """
    if download:
        # instantiate covid19 pdf scraper
        pdf = PdfScraper()
        pdf.get_pages()

        # covid19 cases
        cases = pdf.get_data(marker='line list of cases')
        deaths = pdf.get_data(marker='line list of deaths')

        _db = DataBase()
        _db.add_table(FL_CASES_TABLE, cases, index=False)
        _db.add_table(FL_DEATHS_TABLE, deaths, index=False)
        _db.close()

    else:

        # read from database
        _db = DataBase()
        cases = _db.get_table(FL_CASES_TABLE, parse_dates=['date'])
        deaths = _db.get_table(FL_DEATHS_TABLE, parse_dates=['date'])
        _db.close()

    return cases, deaths


def clean_data(table):
    """clean florida dem data

    Arguments:
        table {String} -- database table name

    Returns:
        DataFrame -- cleaned data
    """
    _db = DataBase()
    data = _db.get_table(table, parse_dates=['date'])
    counties = _db.get_geotable(US_MAP_TABLE)
    _db.close()

    data.loc[data['county'] == 'Dade', 'county'] = 'Miami-Dade'
    lookup = counties[counties['state_id'] == '12'][['county_id', 'name']]
    lookup = lookup.set_index('name')['county_id'].to_dict()
    data['county_id'] = data['county'].map(lookup)
    data['state_id'] = '12'

    start = len(data)

    # drop data in which county or age is unknown
    data = data[~data['county_id'].isna() & ~data['age'].isna()].copy(deep=True)
    data['age'] = np.int32(data['age'])

    # drop data of unknown gender
    data = data[data['gender'] != 'Unknown'].copy(deep=True)
    data['male'] = data['gender'].map({'Male': 1, 'Female': 0})

    # traveled related and contact with known covid19 patient
    data['traveled'] = data['traveled'].map({'Yes': 1, 'No': 0})
    data['contacted'] = data['contacted'].map({'Yes': 1, 'No': 0})
    data['place'] = [x if str(x) == 'nan' else str(x).upper() for x in data['place']]

    # florida residency
    resident = {'FL resident': 1, 'Non-Fl resident': 0}
    data['resident'] = data['resident'].map(resident)

    delta_day = pd.to_timedelta(1, unit='days')
    data['day'] = (data['date'] - data['date'].min()) / delta_day
    data['day'] = data['day'].astype('Int32')

    # select columns and rename case to case_id
    data = data[['case', 'county_id', 'state_id', 'date', 'day', 'male', 'age',
                 'traveled', 'place', 'contacted', 'resident']]
    data = data.rename(columns={'case': 'case_id'})

    end = len(data)

    # ignored lines
    print(f'ignored lines: {start-end}/{start} = {(100*(start-end)/start):.01f}%')

    return data


def download_fldem():
    """Get, clean and store covid19 data from FL DEM
    """
    get_data(True)

    _db = DataBase()

    # cases
    data = clean_data(FL_CASES_TABLE)
    _db.add_table(FLDEM_CASES_TABLE, data.set_index('case_id'))

    # deaths
    data = clean_data(FL_DEATHS_TABLE)
    _db.add_table(FLDEM_DEATHS_TABLE, data.set_index('case_id'))

    # view
    _db.update(DROP_FLDEM_VIEW)
    _db.update(FLDEM_VIEW)

    _db.close()


if __name__ == "__main__":

    # unit test
    download_fldem()
