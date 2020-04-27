# %%
import numpy as np
import pandas as pd
import geopandas as gpd

import matplotlib.pyplot as plt
from shapely.geometry import Polygon, MultiPolygon
from shapely.wkt import loads
from warnings import simplefilter
import re

# path to files
inputpath = './input/'
outputpath = './output/'
datapath = './data/'
shapepath = './shapes/'
htmlpath = './docs/'

# covid19 data
covidpath = datapath + 'us-counties.csv'

# census shape files
countiespath = shapepath + 'counties_500k/cb_2018_us_county_500k.shx'
statepath = shapepath + 'states_500k/cb_2018_us_state_500k.shx'

# clean shape files
us_map_path = shapepath + 'us_map/us_map.shx'
state_map_path = shapepath + 'state_map/state_map.shx'

# lookup files
lookuppath = inputpath + 'fips-county-lookup.csv'


def merge_data(df, map, levels, days):
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
        slice = df_date.set_index('fips').to_dict()

        # add cases and deaths to us_map
        map[f'c{i}'] = map['area_fips'].map(slice['cases']).fillna(0)
        map[f'd{i}'] = map['area_fips'].map(slice['deaths']).fillna(0)

        map[f'm{i}'] = pd.cut(map[f'c{i}'], levels, labels=range(1, len(levels)))

        # fill nans and convert to numeric
        map[f'm{i}'] = pd.to_numeric(map[f'm{i}'], 'coerce').fillna(0).astype('Int32')

    # make current lastest date
    map['c'] = map['c0']
    map['d'] = map['d0']
    map['m'] = map['m0']
    map['day'] = 0

    map.drop(['area_fips'], axis=1, inplace=True)

    return map, dates

def covid_data(df, lookup):

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


def remove_islands(map, min_area=100000000):
    """ Remove small polygons
        Removes polygons with area less than min_area.
           inputs: map, geopandas dataframe
           output: map
           Expects map crs = 'EPSG:3395'
    """

    # convert to dictionary for speed
    records = map.to_dict(orient='records')

    for record in records:
        newgeometry = []
        max_area = 0
        max_area_geometry = Polygon()
        if record['geometry'].type == 'MultiPolygon':
            for geometry in record['geometry']:
                area = geometry.area
                if max_area < geometry.area:
                    max_area = area
                    max_area_geometry = geometry
                if area > min_area:
                    newgeometry.append(geometry)
            if len(newgeometry) > 0:
                record['geometry'] = MultiPolygon(newgeometry)
            else:
                record['geometry'] = geometry

    new_map = gpd.GeoDataFrame(records)

    return new_map

def mround(match):
    return "{:.2f}".format(float(match.group()))

def get_maps():
    # read shape files
    us_map = gpd.read_file(countiespath)
    state_map = gpd.read_file(statepath)
    lookup = pd.read_csv(lookuppath)

    # remove unwanted states
    drop = ['72', '78', '69', '66', '60']
    us_map = us_map[~us_map['STATEFP'].isin(drop)].copy(deep=True)
    state_map = state_map[~state_map['STATEFP'].isin(drop)].copy(deep=True)
    state_fp_dict = dict(zip(state_map.STATEFP, state_map.STUSPS))

    # coordinate reference system
    CRS = 'EPSG:3395'
    simplefilter(action='ignore', category=FutureWarning)
    us_map = us_map.to_crs(CRS)
    state_map = state_map.to_crs(CRS)
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
    [(xt, yt)] = list(state_map.loc[texas, 'geometry'].iat[0].centroid.coords)

    alaska = state_map['STATEFP'] == '02'
    xa = state_map.loc[alaska, 'xc'].iat[0]
    ya = state_map.loc[alaska, 'yc'].iat[0]

    hawaii = state_map['STATEFP'] == '15'
    xh = state_map.loc[hawaii, 'xc'].iat[0]
    yh = state_map.loc[hawaii, 'yc'].iat[0]

    state_map.loc[alaska, 'geometry'] = state_map[alaska].scale(
                    xfact=0.19, yfact=0.19, zfact=1.0, origin='centroid')
    state_map.loc[alaska, 'geometry'] = state_map[alaska].translate(
                    xoff=xt-xa-2.7e6, yoff=yt-ya-5.0e5, zoff=0.0)
    state_map.loc[hawaii, 'geometry'] = state_map[hawaii].translate(
                    xoff=xt-xh-1.5e6, yoff=yt-yh-7.5e5, zoff=0.0)

    alaska_ct = us_map['STATEFP'] == '02'
    hawaii_ct = us_map['STATEFP'] == '15'
    us_map.loc[alaska_ct, 'geometry'] = us_map[alaska_ct].scale(
                    xfact=0.19, yfact=0.19, zfact=1.0, origin=(xa, ya, 0))
    us_map.loc[alaska_ct, 'geometry'] = us_map[alaska_ct].translate(
                    xoff=xt-xa-2.7e6, yoff=yt-ya-5.0e5, zoff=0.0)
    us_map.loc[hawaii_ct, 'geometry'] = us_map[hawaii_ct].translate(
                    xoff=xt-xh-1.5e6, yoff=yt-yh-7.5e5, zoff=0.0)

    # remove small island (second pass)
    us_map = remove_islands(us_map)
    state_map = remove_islands(state_map)

    # smooth out polygons
    dist = 3500
    us_map['geometry'] = gpd.GeoSeries([x if x.type != 'Polygon' else
        Polygon(x.buffer(dist, join_style=1).buffer(-1*dist, join_style=1))
        for x in us_map['geometry']])

    state_map['geometry'] = gpd.GeoSeries([x if x.type != 'Polygon' else
        Polygon(x.buffer(dist, join_style=1).buffer(-1*dist, join_style=1))
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

# %% create lookup
def create_lookups():
    df = pd.read_csv(inputpath + 'state-lookup.csv', dtype={'STATEFP': object})
    df1 = pd.read_csv(inputpath + 'abbr-name.csv')
    df1['name'] = df1['name'].str.lower()
    df['abbr'] = df['NAME'].str.lower().map(df1.set_index('name')['abbr'])
    df.to_csv(inputpath + 'abbr-name.csv', index=False)


if __name__ == "__main__":

    # unit test
    us_map, state_map = get_maps()
    us_map.to_file(shapepath + 'us_map/us_map.shp')
    state_map.to_file(shapepath + 'state_map/state_map.shp')

    if False: # unit testing
        us_map = gpd.read_file('./shapes/us_map/us_alaska.shx')
        state_map = gpd.read_file('./shapes/state_map/state_alaska.shx')

        texas = state_map['STATEFP'] == '48'
        [(xt, yt)] = list(state_map.loc[texas, 'geometry'].iat[0].centroid.coords)

        alaska = state_map['STATEFP'] == '02'
        xa = state_map.loc[alaska, 'xc'].iat[0]
        ya = state_map.loc[alaska, 'yc'].iat[0]

        hawaii = state_map['STATEFP'] == '15'
        xh = state_map.loc[hawaii, 'xc'].iat[0]
        yh = state_map.loc[hawaii, 'yc'].iat[0]

        # state map scale and translate alaska and hawaii
        state_map.loc[alaska, 'geometry'] = state_map[alaska].scale(
                    xfact=0.19, yfact=0.19, zfact=1.0, origin='centroid')
        state_map.loc[alaska, 'geometry'] = state_map[alaska].translate(
                    xoff=xt-xa-2.7e6, yoff=yt-ya-5.0e5, zoff=0.0)
        state_map.loc[hawaii, 'geometry'] = state_map[hawaii].translate(
                    xoff=xt-xh-1.5e6, yoff=yt-yh-7.5e5, zoff=0.0)

        # us map scale and translate alaska and hawaii
        alaska_ct = us_map['STATEFP'] == '02'
        hawaii_ct = us_map['STATEFP'] == '15'
        us_map.loc[alaska_ct, 'geometry'] = us_map[alaska_ct].scale(
                    xfact=0.19, yfact=0.19, zfact=1.0, origin=(xa, ya, 0))
        us_map.loc[alaska_ct, 'geometry'] = us_map[alaska_ct].translate(
                    xoff=xt-xa-2.7e6, yoff=yt-ya-5.0e5, zoff=0.0)
        us_map.loc[hawaii_ct, 'geometry'] = us_map[hawaii_ct].translate(
                    xoff=xt-xh-1.5e6, yoff=yt-yh-7.5e5, zoff=0.0)

        # remove small island in alaska
        us_map = remove_islands(us_map)
        state_map = remove_islands(state_map)

        # create the plot for Arkansas
        fig, ax = plt.subplots(figsize=(10,6))
        state_map[~(alaska | hawaii)].plot(column='NAME', ax=ax)
        state_map[alaska].plot(ax=ax, color='black')
        state_map[hawaii].plot(ax=ax, color='blue')
        plt.axis('equal');

        fig, ax = plt.subplots(figsize=(10,6))
        us_map[~(alaska_ct | hawaii_ct)].plot(column='NAME', ax=ax)
        us_map[alaska_ct].plot(ax=ax, color='black')
        us_map[hawaii_ct].plot(ax=ax, color='blue')
        plt.axis('equal');
