"""
   Data cleaning and formating module
"""

from os.path import join
from warnings import simplefilter
import re

import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import (
    Polygon,
    MultiPolygon
)
from shapely.wkt import loads

from utilities import cwd
from database import DataBase


# inputs
COUNTY_SHAPES = join(cwd(), 'shapes', 'counties_500k', 'cb_2018_us_county_500k.shx')
STATE_SHAPES = join(cwd(), 'shapes', 'states_500k', 'cb_2018_us_state_500k.shx')

# outputs
US_MAP_TABLE = 'us_map'
STATE_MAP_TABLE = 'state_map'


def remove_islands(map_file, min_area=100000000):
    """Remove small polygons

    Arguments:
        map_file {GeoDataFrame} -- data with a 'geometry' column and
                                   expected crs = 'EPSG:3395

    Keyword Arguments:
        min_area {int} -- polygon area to remove (default: {100000000})

    Returns:
        GeoDataFrame -- data with small polygon removed
    """
    records = map_file.to_dict(orient='records')
    for record in records:
        if record['geometry'].type == 'MultiPolygon':
            multipoly = list(record['geometry'])
            polies = [poly for poly in multipoly if poly.area > min_area]
            if polies:
                record['geometry'] = MultiPolygon(polies)
            else:
                record['geometry'] = max(
                    record['geometry'], key=lambda a: a.area)

    new_map = gpd.GeoDataFrame(records)

    return new_map


def mround(match):
    """Return formated string
    """
    return "{:.2f}".format(float(match.group()))


def transform_alaska_hawaii(us_map, state_map):
    """[summary]

    Arguments:
        us_map {GeoDataFrame} -- us counties geodataframe
        state_map {[type]} -- us states geodataframe

    Returns:
        tuple -- tuple of dataframes with alaska and hawaii transformed
    """
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

    return us_map, state_map


def group_nyc_counties(us_map):
    """Group NYC counties as New York City

    Arguments:
        us_map {GeoDataFrame} -- county metadata

    Returns:
        {GeoDataFrame} -- county metadata
    """
    # new york city counties
    nyc_counties = {'Queens': '36081',
                    'Bronx': '36005',
                    'Richmond': '36085',
                    'New York': '36061',
                    'Kings': '36047'}

    nyc = us_map.loc[us_map['county_id'].isin(nyc_counties.values()), :]
    nyc = nyc.copy(deep=True)

    nyc['county_id'] = '36061'
    nyc = nyc.dissolve(by='county_id', aggfunc='sum').reset_index()
    nyc['name'] = 'New York City'
    nyc['state_id'] = '36'

    counties = us_map.loc[~us_map['county_id'].isin(nyc_counties.values()), :]
    counties = counties.copy(deep=True)
    counties = counties.append(nyc, ignore_index=True)

    return counties


def get_maps(us_map, state_map):
    """Shapes transformation of county and state maps

    Arguments:
        us_map {GeoDataFrame} -- us county map
        state_map {[type]} -- us state map

    Returns:
        tuple -- transformed us_map and state_map
    """
    # remove unwanted states
    drop = ['72', '78', '69', '66', '60']
    us_map = us_map[~us_map['STATEFP'].isin(drop)].copy(deep=True)
    state_map = state_map[~state_map['STATEFP'].isin(drop)].copy(deep=True)

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

    # scale Alaska and move Alaska and Hawaii under California
    us_map, state_map = transform_alaska_hawaii(us_map, state_map)

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

    # simplify geometry
    tolerance = 2000
    us_map['geometry'] = us_map['geometry'].simplify(tolerance)
    state_map['geometry'] = state_map['geometry'].simplify(tolerance)

    # dissolve us map by county
    us_map['DISSOLVE'] = us_map['NAME'] + us_map['STATEFP']
    us_map = us_map.dissolve('DISSOLVE')
    us_map.reset_index(drop=True, inplace=True)

    # dissolve state map by state
    state_map = state_map.dissolve('STATEFP')
    state_map.reset_index(inplace=True)

    # remove holes from polygons
    us_map['geometry'] = gpd.GeoSeries(
        [x if x.type != 'Polygon' else Polygon(x.exterior) for x in us_map['geometry']])
    state_map['geometry'] = gpd.GeoSeries(
        [x if x.type != 'Polygon' else Polygon(x.exterior) for x in state_map['geometry']])

    # create unique ids
    us_map['fips'] = us_map['GEOID'].astype(int)

    # add population data from lookup
    pop = pd.read_csv(join(cwd(), 'input', 'fips_county_pop.csv'))
    pop = pop.set_index('fips')['population'].to_dict()
    us_map['pop'] = us_map['fips'].map(pop)
    us_map['pop'].fillna(0)

    pop = pd.read_csv(join(cwd(), 'input', 'state_name_pop.csv'))
    pop = pop.set_index('state')['pop'].to_dict()
    state_map['pop'] = state_map['NAME'].map(pop)

    # select columns, covert to lowercase, and change column names
    keep = ['GEOID', 'STATEFP', 'NAME', 'ALAND', 'AWATER', 'pop', 'geometry']
    us_map = us_map[keep].dropna().copy(deep=True)
    us_map = us_map.rename(columns={'GEOID': 'county_id', 'STATEFP': 'state_id'})
    us_map.columns = [name.lower() for name in us_map.columns]

    keep = ['STATEFP', 'NAME', 'STUSPS', 'ALAND', 'AWATER', 'pop', 'geometry']
    state_map = state_map[keep].dropna().copy(deep=True)
    state_map = state_map.rename(columns={'STATEFP': 'state_id', 'STUSPS': 'abbr'})
    state_map.columns = [name.lower() for name in state_map.columns]

    # convert land area (aland) and water area (awater) to square km
    us_map[['aland', 'awater']] = np.int32(us_map[['aland', 'awater']]/1e6)
    state_map[['aland', 'awater']] = np.int32(state_map[['aland', 'awater']]/1e6)

    # group new york city counties as one (new york city)
    us_map = group_nyc_counties(us_map)

    # finally round geometry coords to two decimal points
    us_map['geometry'] = us_map['geometry'].apply(
        lambda x: loads(re.sub(r'\d*\.\d+', mround, x.wkt)))
    state_map['geometry'] = state_map['geometry'].apply(
        lambda x: loads(re.sub(r'\d*\.\d+', mround, x.wkt)))

    return us_map, state_map

def maps_to_database():
    """Refresh database with counties and states map
    """
    us_map = gpd.read_file(COUNTY_SHAPES, encoding='UTF-8')
    state_map = gpd.read_file(STATE_SHAPES, encoding='UTF-8')

    # format shapes files
    us_map, state_map = get_maps(us_map, state_map)

    # to database
    _db = DataBase()
    _db.add_geotable(US_MAP_TABLE, us_map)
    _db.add_geotable(STATE_MAP_TABLE, state_map)
    _db.close()


if __name__ == "__main__":

    maps_to_database()
