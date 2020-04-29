"""
    This module read pdf COVID-19 file from Florida Division of Emergency
    Management and save it into a CSV format
"""

from io import BytesIO
from os import getcwd
from os.path import dirname, join
import re
import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
import PyPDF2

# pylint: disable=invalid-name

def cwd():
    """
        Return current working dictory when __file__ is available
        otherwise request info from OS.
    """

    try:
        __file__
    except NameError:
        current_working_dir = getcwd()
    else:
        current_working_dir = dirname(__file__)
    return current_working_dir


def get_pdf_name(url, class_dict):
    """
        Get pdf name from URL.
    """

    with requests.Session() as s:
        s.trust_env = False
        download = s.get(url)
        html = download.text

    #soup = BeautifulSoup(html, features='lxml')
    soup = BeautifulSoup(html, features="html.parser")
    body = soup.find('div', class_dict)
    paragraphs = body.find_all('p')

    data = []
    for paragraph in paragraphs:
        sentences = paragraph.find_all('a')
        data.append(str(sentences[0]))

    line = [line for line in data if
            re.search(r'COVID-19 Data - Daily Report', line)][0]

    try:
        pdfname = re.search(r'\"(.+?)\"', line).group(1)
    except AttributeError:
        # ", " not found in the original string
        pdfname = 'NA'
    return pdfname


def pdf_to_text(path, marker, read_from):
    """
        Return text from pdf file
    """

    if read_from == 'memory':
        # creating a pdf file object
        with open(path, 'rb') as pdf:
            reader = PyPDF2.PdfFileReader(pdf)
    elif read_from == 'url':
        reader = PyPDF2.PdfFileReader(path)

    # extract text from each pdf page
    pages = []
    for page in range(reader.numPages):
        pagetext = reader.getPage(page).extractText()
        if re.search(marker, pagetext):
            pages.append(pagetext)

    # unwanted lines contains these words
    regex = re.compile(('Data|Death|County|Age|Gender|Travel|related|'
                        'Contact|confirmed|Jurisdiction|Date|counted|'
                        'today|Coronavirus|case'), re.IGNORECASE)

    pageList = [page.split('\n') for page in pages]
    lines = [line for page in pageList for line in page
             if not re.search(regex, line)]

    return lines


def read_data(path, marker, read_from='memory'):
    """
        read pdf file and convert content to dataframe
    """

    lines = pdf_to_text(path, marker, read_from)

    outter = []
    inner = []
    for line in lines:
        if line != "":
            inner.append(line)
            if re.search(r'\d{2}\/', line):
                while inner:
                    if inner[0].replace(',', '').strip().isnumeric():
                        break
                    else:
                        del inner[0]
                if len(inner) == 7:
                    inner.insert(4, 'Unknown')
                if len(inner) == 8:
                    inner.insert(5, 'NaN')
                if len(inner) == 10:
                    inner[5] = inner[5].join(inner[6])
                    del inner[6]
                outter.append(inner)
                inner = []

    # create dataframe with extracted data
    rows = [row for row in outter if len(row) == 9]
    df = pd.DataFrame(rows,
                      columns=['case', 'county', 'age', 'gender', 'traveled',
                               'where', 'contacted', 'resident', 'date'])

    # format data
    df['case'] = pd.to_numeric(
        df['case'].str.replace(',', ''), errors='coerce')
    df['age'] = pd.to_numeric(df['age'], errors='coerce')
    df['datetime'] = pd.to_datetime(df['date'], format='%m/%d/%y')

    # sort by datetime
    df.sort_values('datetime', inplace=True)
    df.reset_index(drop=True, inplace=True)

    return df


def get_data(download=False):
    """
        Get FDEM data and save it.
    """

    if download:
        base_url = 'https://floridadisaster.org'
        pdfname = get_pdf_name(url=base_url + '/covid19/',
                               class_dict={'class': 'panel-body'})
        pdf_url = base_url + pdfname

        # get report in pdf from pdf_url
        with requests.Session() as s:
            s.trust_env = False
            response = s.get(pdf_url)
            pdffile = response.content

        # tabulate data
        cases = read_data(path=BytesIO(pdffile),
                          marker='line list of cases', read_from='url')
        cases.to_csv(join(cwd(), 'output', 'fl_cases.csv'), index=False)

        deaths = read_data(path=BytesIO(pdffile),
                           marker='line list of death', read_from='url')
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

        numrows = len(cases.loc[slicer, :])
        if numrows == 1:
            cases.loc[slicer, 'died'] = 1
        elif numrows > 1:
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

    # lat, lon - convert to cartesian cordinates
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

STAND_ALONE = False
if STAND_ALONE:
    # unit test
    download_fldem()
