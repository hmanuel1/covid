"""
    Read pdf COVID-19 file from Florida Division of Emergency
    Management and save it into a CSV format
"""
# %%
from os.path import join
from io import BytesIO
import re

import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
import PyPDF2

from utilities import cwd


# base url
BASE_URL = 'https://floridadisaster.org'

# covid19 url
COVID19_URL = 'https://floridadisaster.org/covid19/'


class PdfScraper:
    """
        This class read a pdf file from an url and transform text
        into a pandas dataframe.
    """

    def __init__(self):
        self.url = None
        self.pages = None
        self.lines = None
        self.data = None

        # get pdf file url
        self.__get_url(COVID19_URL)

    def __get_url(self, url):
        """ get url of pdf file
        """

        # get html
        _response = requests.get(url)
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
            self.url = BASE_URL + _match.group(1)
        else:
            self.url = 'NA'

    def get_pages(self):
        """
            get pdf pages in text
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
        """
            get pdf in text format
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
        """ read pdf file from url """

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
        _cols = ['case', 'county', 'age', 'gender', 'traveled', 'where',
                 'contacted', 'resident', 'date']

        # enter data in data frame and format
        self.data = pd.DataFrame(_rows, columns=_cols)
        self.data['age'] = pd.to_numeric(self.data['age'], errors='coerce')
        self.data['datetime'] = pd.to_datetime(self.data['date'], format='%m/%d/%y')

        # sort by datetime
        self.data.sort_values('datetime', inplace=True)
        self.data.reset_index(drop=True, inplace=True)

        return self.data


def get_data(download=False):
    """
        Get FDEM data and save it.
    """

    if download:
        # instantiate covid19 pdf scraper
        pdf = PdfScraper()
        pdf.get_pages()

        # covid19 cases
        cases = pdf.get_data(marker='line list of cases')
        cases.to_csv(join(cwd(), 'output', 'fl_cases.csv'), index=False)

        # covid19 deaths
        deaths = pdf.get_data(marker='line list of deaths')
        deaths.to_csv(join(cwd(), 'output', 'fl_deaths.csv'), index=False)
    else:
        # read data from memory
        cases = pd.read_csv(join(cwd(), 'output', 'fl_cases.csv'))
        deaths = pd.read_csv(join(cwd(), 'output', 'fl_deaths.csv'))

        # convert date to datetime
        cases['datetime'] = pd.to_datetime(cases['date'], format='%m/%d/%y')
        deaths['datetime'] = pd.to_datetime(deaths['date'], format='%m/%d/%y')
    return cases, deaths


def add_deaths(cases, deaths):
    """
        Add covid19 deaths to cases
    """

    cases['died'] = 0
    for row in deaths.itertuples():
        slicer = ((cases['county'] == row.county) & (cases['age'] == row.age) &
                  (cases['gender'] == row.gender) & (cases['date'] == row.date) &
                  (cases['traveled'] == row.traveled) &
                  (cases['contacted'] == row.contacted))

        num_rows = len(cases.loc[slicer, :])
        if num_rows == 1:
            cases.loc[slicer, 'died'] = 1
        elif num_rows > 1:
            cases.loc[cases[slicer].tail(1).index, 'died'] = 1
        else:
            print('Error: case not found!')
    return cases


def fl_clean_data(download=False):
    """ Florida Clean Data
       Get Florida covid19 data and clean it

       Input: download, True if need to get an update from web
       Output: df, dataframe with data cleaned
    """

    # get florida data
    cases, deaths = get_data(download)
    cases = add_deaths(cases, deaths)
    cases.loc[cases['county'] == 'Dade', 'county'] = 'Miami-Dade'
    cases = cases[cases['gender'].isin(['Male', 'Female'])].copy(deep=True)
    cases['key'] = cases['county'] + ', FL'

    # get counties data
    counties = pd.read_csv(join(cwd(), 'input', 'counties_lat_lon.csv'))
    counties = counties[counties['state'] == 'FL'].copy(deep=True)
    counties['key'] = counties['county'] + ', FL'

    # add county data to covid19 data
    df = cases.merge(counties, on='county', how='left')
    df = df[['died', 'datetime', 'fips', 'age', 'gender',
             'population', 'land_sqkm', 'water_sqkm',
             'lat', 'lon']].copy(deep=True)

    # datetime - convert datetimes to linear days, starting from earliest date
    delta_day = pd.to_timedelta(1, unit='days')
    df['datetime'] = (df['datetime'] - df['datetime'].min()) / delta_day
    df['datetime'] = df['datetime'].astype('Int32')

    # gender - get dummies
    df = pd.concat([df, pd.get_dummies(df['gender'], drop_first=True)], axis=1)
    df.drop(['gender'], axis=1, inplace=True)

    # lat, lon - convert to cartesian coordinates
    df['dx'] = (df['lon'] - df['lat'])
    df['dx'] = df['dx'] * 40000 * \
        np.cos((df['lat'] - df['lon']) * np.pi / 360) / 360
    df['dx'] = df['dx'].round(2)
    df['dy'] = ((df['lat'] - df['lon']) * 40000 / 360).round(2)
    df.drop(['lat', 'lon'], axis=1, inplace=True)

    # density - calculate population density
    df['density'] = (df['population'] / df['land_sqkm']).round(1)

    return df

def download_fldem():
    """
        main function of module to download, clean and save data
    """

    df = fl_clean_data(download=True)
    df.to_csv(join(cwd(), 'data', 'flclean.csv'), index=False)

if __name__ == "__main__":

    # unit test
    download_fldem()
