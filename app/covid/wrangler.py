"""
   Data cleaning and formating module
"""

from os.path import join
from warnings import simplefilter
import re

import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon
from shapely.wkt import loads

from utilities import cwd

# pylint: disable=too-many-statements, too-many-locals

# us census shape file paths
COUNTY_SHAPES = join(cwd(), 'shapes', 'counties_500k', 'cb_2018_us_county_500k.shx')
STATE_SHAPES = join(cwd(), 'shapes', 'states_500k', 'cb_2018_us_state_500k.shx')

# lookup files
LOOKUP_FIPS = join(cwd(), 'input', 'fips-county-lookup.csv')

def merge_data(df, us_map, levels, days):
    """
        Merge COVID-19 data with us_map data
    """
    # calculate dates
    dates = []
    latest_date = df['date'].max()
    for day in range(days):
        date = latest_date - pd.to_timedelta(day, 'days')
        dates.append(date)

    # add covid19 data to us_map
    for i, date in enumerate(dates):
        # get cumulative date up to this date
        df_date = df[['fips', 'cases', 'deaths']][df['date'] == date]
        slicer = df_date.set_index('fips').to_dict()

        # add cases and deaths to us_map
        us_map[f'c{i}'] = us_map['area_fips'].map(slicer['cases']).fillna(0)
        us_map[f'd{i}'] = us_map['area_fips'].map(slicer['deaths']).fillna(0)

        us_map[f'm{i}'] = pd.cut(us_map[f'c{i}'], levels,
                                 labels=range(1, len(levels)))

        # fill nans and convert to numeric
        us_map[f'm{i}'] = pd.to_numeric(
            us_map[f'm{i}'], 'coerce').fillna(0).astype('Int32')

    # make current lastest date
    us_map['c'] = us_map['c0']
    us_map['d'] = us_map['d0']
    us_map['m'] = us_map['m0']
    us_map['day'] = 0

    us_map.drop(['area_fips'], axis=1, inplace=True)

    return us_map, dates

def covid_data(df, lookup):
    """
        Cleanup COVID-19 data from NY Times
    """

    # assign Manhattan fips to New York City
    nyc_fips = 3600
    df.loc[df['county'] == 'New York City', 'fips'] = nyc_fips

    # remove boroughs from covid19 dataset
    boroughs = {'Queens': 36081, 'Bronx': 36005,
                'Richmond': 36085, 'Brooklyn': 36047}
    df = df[~df['fips'].isin(boroughs.values())].copy(deep=True)
    df['adj'] = False

    # fill nyc boroughs with nyc data
    nydf = df[df['fips'] == nyc_fips].copy(deep=True)
    for borough in boroughs:
        nydf['county'] = borough
        nydf['fips'] = boroughs[borough]
        nydf['adj'] = True
        df = pd.concat([df, nydf], axis=0, ignore_index=True)

    # drop rows with no defined fips
    df.dropna(inplace=True)
    df['fips'] = df['fips'].astype('Int32')
    df.sort_values(['fips', 'date'], ascending=True, inplace=True)
    df.reset_index(drop=True, inplace=True)

    # add name [county, State Abrevation]
    lookup['name'] = lookup['name'].str.lower()
    abbr = lookup.set_index('name')['abbr']
    df['name'] = df['county'] + ', ' + df['state'].str.lower().map(abbr)
    return df

def remove_islands(map_file, min_area=100000000):
    """ Remove small polygons
        Removes polygons with area less than min_area.
           inputs: map_file, geopandas dataframe
           output: map_file
           Expects map_file crs = 'EPSG:3395'
    """

    # convert to dictionary for speed
    records = map_file.to_dict(orient='records')

    for record in records:
        newgeometry = []
        max_area = 0
        if record['geometry'].type == 'MultiPolygon':
            for geometry in record['geometry']:
                area = geometry.area
                if max_area < geometry.area:
                    max_area = area
                if area > min_area:
                    newgeometry.append(geometry)
            if newgeometry:
                record['geometry'] = MultiPolygon(newgeometry)
            else:
                record['geometry'] = Polygon()

    new_map = gpd.GeoDataFrame(records)

    return new_map

def mround(match):
    """
        Return formated string
    """

    return "{:.2f}".format(float(match.group()))


def get_maps(us_map, state_map):
    """
        Take shape files and lower resolution of shapes
    """

    # read shape files
    lookup = pd.read_csv(LOOKUP_FIPS)

    # remove unwanted states
    drop = ['72', '78', '69', '66', '60']
    us_map = us_map[~us_map['STATEFP'].isin(drop)].copy(deep=True)
    state_map = state_map[~state_map['STATEFP'].isin(drop)].copy(deep=True)
    state_fp_dict = dict(zip(state_map.STATEFP, state_map.STUSPS))

    # coordinate reference system
    simplefilter(action='ignore', category=FutureWarning)
    us_map = us_map.to_crs('EPSG:3395')
    state_map = state_map.to_crs('EPSG:3395')
    simplefilter(action='default')

    # remove islands (first pass)
    us_map = remove_islands(us_map)
    state_map = remove_islands(state_map)

    # add centroids to state map
    points = list(state_map['geometry'].centroid)
    state_map['xc'] = [point.coords[0][0] for point in points]
    state_map['yc'] = [point.coords[0][1] for point in points]

    # transform alaska and hawaii
    texas = state_map['STATEFP'] == '48'
    [(xc_tx, yc_tx)] = list(state_map.loc[texas, 'geometry'].iat[0].centroid.coords)

    alaska = state_map['STATEFP'] == '02'
    xc_ak = state_map.loc[alaska, 'xc'].iat[0]
    yc_ak = state_map.loc[alaska, 'yc'].iat[0]

    hawaii = state_map['STATEFP'] == '15'
    xc_hi = state_map.loc[hawaii, 'xc'].iat[0]
    yc_hi = state_map.loc[hawaii, 'yc'].iat[0]

    state_map.loc[alaska, 'geometry'] = state_map[alaska].scale(
        xfact=0.19, yfact=0.19, zfact=1.0, origin='centroid')
    state_map.loc[alaska, 'geometry'] = state_map[alaska].translate(
        xoff=xc_tx - xc_ak - 2.7e6, yoff=yc_tx - yc_ak - 5.0e5, zoff=0.0)
    state_map.loc[hawaii, 'geometry'] = state_map[hawaii].translate(
        xoff=xc_tx - xc_hi - 1.5e6, yoff=yc_tx - yc_hi - 7.5e5, zoff=0.0)

    alaska_ct = us_map['STATEFP'] == '02'
    hawaii_ct = us_map['STATEFP'] == '15'
    us_map.loc[alaska_ct, 'geometry'] = us_map[alaska_ct].scale(
        xfact=0.19, yfact=0.19, zfact=1.0, origin=(xc_ak, yc_ak, 0))
    us_map.loc[alaska_ct, 'geometry'] = us_map[alaska_ct].translate(
        xoff=xc_tx - xc_ak - 2.7e6, yoff=yc_tx - yc_ak - 5.0e5, zoff=0.0)
    us_map.loc[hawaii_ct, 'geometry'] = us_map[hawaii_ct].translate(
        xoff=xc_tx - xc_hi - 1.5e6, yoff=yc_tx - yc_hi - 7.5e5, zoff=0.0)

    # remove small island (second pass)
    us_map = remove_islands(us_map)
    state_map = remove_islands(state_map)

    # smooth out polygons
    dist = 3500
    us_map['geometry'] = gpd.GeoSeries([x if x.type != 'Polygon' else Polygon(
        x.buffer(dist, join_style=1).buffer(-1 * dist, join_style=1))
                                        for x in us_map['geometry']])

    state_map['geometry'] = gpd.GeoSeries([x if x.type != 'Polygon' else Polygon(
        x.buffer(dist, join_style=1).buffer(-1 * dist, join_style=1))
                                           for x in state_map['geometry']])

    # symplify geometry
    tolerance = 2000
    us_map['geometry'] = us_map['geometry'].simplify(tolerance)
    state_map['geometry'] = state_map['geometry'].simplify(tolerance)

    # disolve us map by county
    us_map['DISOLVE'] = (us_map['NAME'].str.strip() + ', ' +
                         us_map['STATEFP'].str.strip())
    us_map = us_map.dissolve('DISOLVE')
    us_map.reset_index(drop=True, inplace=True)

    # disolve state map by state
    state_map = state_map.dissolve('STATEFP')
    state_map.reset_index(inplace=True)

    # remove holes from shapes
    us_map['geometry'] = gpd.GeoSeries([x if x.type != 'Polygon' else
                                        Polygon(x.exterior) for x in us_map['geometry']])
    state_map['geometry'] = gpd.GeoSeries([x if x.type != 'Polygon' else
                                           Polygon(x.exterior) for x in state_map['geometry']])

    # create unique ids
    us_map['area_fips'] = (us_map.STATEFP.astype(str) +
                           us_map.COUNTYFP.astype(str))
    us_map['area_fips'] = us_map['area_fips'].astype(int)

    # create county, state names
    us_map['STUSPS'] = us_map['STATEFP'].map(state_fp_dict)
    us_map['NAME'] = us_map['NAME'] + ', ' + us_map['STUSPS']

    # add population data from lookup
    population = lookup.set_index('fips')['population'].to_dict()
    us_map['population'] = us_map['area_fips'].map(population)
    us_map['population'].fillna(0)

    # select columns needed
    keep = ['area_fips', 'STATEFP', 'NAME', 'geometry', 'population']
    us_map = us_map[keep].dropna().copy(deep=True)
    keep = ['STATEFP', 'NAME', 'geometry', 'xc', 'yc']
    state_map = state_map[keep].dropna().copy(deep=True)

    # recalculate centroids in state map
    points = list(state_map['geometry'].centroid)
    state_map['xc'] = [point.coords[0][0] for point in points]
    state_map['yc'] = [point.coords[0][1] for point in points]

    # finally round geometry coords to two decimal points
    us_map['geometry'] = us_map['geometry'].apply(lambda x:
                                                  loads(re.sub(r'\d*\.\d+', mround, x.wkt)))
    state_map['geometry'] = state_map['geometry'].apply(lambda x:
                                                        loads(re.sub(r'\d*\.\d+', mround, x.wkt)))

    return us_map, state_map

def create_lookups():
    """
        Helper function to create lookup table
    """

    df = pd.read_csv(join(cwd(), 'input', 'state-lookup.csv'), dtype={'STATEFP': object})
    df1 = pd.read_csv(join(cwd(), 'input', 'abbr-name.csv'))
    df1['name'] = df1['name'].str.lower()
    df['abbr'] = df['NAME'].str.lower().map(df1.set_index('name')['abbr'])
    df.to_csv(join(cwd(), 'input', 'abbr-name.csv'), index=False)


if __name__ == "__main__":

    # unit test
    us, state = get_maps(gpd.read_file(COUNTY_SHAPES), gpd.read_file(STATE_SHAPES))
    us.to_file(join(cwd(), 'shapes', 'us_map', 'us_map.shp'))
    state.to_file(join(cwd(), 'state_map', 'state_map.shp'))
