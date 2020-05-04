"""App DataBase Interface
"""
from os.path import join

import sqlite3
import pandas as pd
import geopandas as gpd
from shapely import wkb
from utilities import cwd

DB_PATH = join(cwd(), 'data', 'covid19.sqlite3')

class DataBase:
    """Interface with sqlite database

        Examples:

        db = DataBase()

        df = pd.read_csv(path_to_csv)

        db.add_dataframe(table_name, df)

        gdf = gpd.read_file(path_to_shapes)

        db.add_geodata(table_name, gdf)

        gdf = db.get_geodata(table_name)

        db.close()
        """
    def __init__(self, path=DB_PATH):
        """Connect to SQLite database

        Keyword Arguments:
            path {String} -- database file (default: {DB_PATH})
        """
        self.conn = sqlite3.connect(path)
        print('DB connection started')

    def update(self, sql_query):
        """Update database

        Arguments:
            sql_query {String} -- SQL query
        """
        cursor = self.conn.cursor()
        cursor.execute(sql_query)
        self.conn.commit()

    def fetch(self, sql_query):
        """Fetch data from database

        Arguments:
            sql_query {String} -- SQL query

        Returns:
            list -- datbase records
        """
        cursor = self.conn.cursor()
        cursor.execute(sql_query)
        return cursor.fetchall()

    def add_dataframe(self, name, data):
        """Add a pandas table to database

        Arguments:
            name {String} -- table name
            data {DataFrame} -- table data
        """
        data.to_sql(name, con=self.conn, if_exists='replace')

    def add_geodata(self, name, geodata):
        """Add a geopandas table to database

        Arguments:
            name {String} -- table name
            data {GeoDataFrame} -- table data
        """
        _geo = geodata.copy(deep=True)
        _geo['geometry'] = _geo['geometry'].apply(lambda x: x.wkb_hex)
        _geo.to_sql(name, con=self.conn, if_exists='replace')

    def get_dataframe(self, name):
        """Return dataframe from database

        Arguments:
            name {String} -- table name

        Returns:
            {DataFrame} -- table data
        """
        _query = pd.read_sql_query(sql=f"select * from {name}", con=self.conn)

        return pd.DataFrame(_query)

    def get_geodata(self, name):
        """Return geodataframe from database

        Arguments:
            name {String} -- table name

        Returns:
            {GeoDataFrame} -- table data
        """
        _geo = self.get_dataframe(name)
        _geo.drop('index', axis=1, inplace=True)
        _geo['geometry'] = _geo['geometry'].apply(lambda x: wkb.loads(x, hex=True))

        return _geo

    def close(self):
        """Close database connection
        """
        self.conn.close()
        print('DB connection closed')


# add all tables to database
db = DataBase()

# shapes
gdf = gpd.read_file(join(cwd(), 'shapes', 'us_map', 'us_map.shx'))
db.add_geodata(name='us_map', geodata=gdf)

gdf = gpd.read_file(join(cwd(), 'shapes', 'state_map', 'state_map.shx'))
db.add_geodata(name='state_map', geodata=gdf)

# raw data ny times
df = pd.read_csv(join(cwd(), 'data', 'us-counties.csv'))
db.add_dataframe(name='us_counties', data=df)

df = pd.read_csv(join(cwd(), 'data', 'us-states.csv'))
db.add_dataframe(name='us_states', data=df)

# raw data fl dem
df = pd.read_csv(join(cwd(), 'output', 'fl_cases.csv'))
db.add_dataframe(name='fldem_cases', data=df)

df = pd.read_csv(join(cwd(), 'output', 'fl_deaths.csv'))
db.add_dataframe(name='fldem_deaths', data=df)

# predicted fl cases and deaths using ny times data
df = pd.read_csv(join(cwd(), 'output', 'arima-cases.csv'))
db.add_dataframe(name='arima_cases', data=df)

df = pd.read_csv(join(cwd(), 'output', 'arima-deaths.csv'))
db.add_dataframe(name='arima_deaths', data=df)

# classification results of deaths from fl dem data
df = pd.read_csv(join(cwd(), 'output', 'fl_fi_models.csv'))
db.add_dataframe(name='importance', data=df)

df = pd.read_csv(join(cwd(), 'output', 'fl_roc_models.csv'))
db.add_dataframe(name='models_roc', data=df)

db.close()
