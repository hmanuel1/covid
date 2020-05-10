"""App DataBase Interface
"""

from os.path import join

import sqlite3
import pandas as pd
import geopandas as gpd
from shapely import wkb
from utilities import cwd

DATABASE_PATH = join(cwd(), 'data', 'covid19.sqlite3')
TRACING = True

class DataBase:
    """Interface with sqlite database

        Examples:

        database = DataBase()

        df = pd.read_csv(path_to_csv)

        database.add_table(table_name, df)

        gdf = gpd.read_file(path_to_shapes)

        database.add_geotable(table_name, gdf)

        gdf = database.get_geotable(table_name)

        database.close()
        """
    def __init__(self, path=DATABASE_PATH):
        """Connect to SQLite database

        Keyword Arguments:
            path {String} -- database file (default: {DATABASE_PATH})
        """
        self.conn = sqlite3.connect(path)
        if TRACING:
            print('database connection started')

    def update(self, sql_query):
        """Update database

        Arguments:
            sql_query {String} -- SQL query
        """
        cursor = self.conn.cursor()
        cursor.execute(sql_query + ';')
        self.conn.commit()
        if TRACING:
            print('update executed')

    def fetch(self, sql_query):
        """Fetch data from database

        Arguments:
            sql_query {String} -- SQL query

        Returns:
            list -- datbase records
        """
        cursor = self.conn.cursor()
        cursor.execute(sql_query + ';')
        return cursor.fetchall()

    def add_table(self, name, data, index=True):
        """Add a pandas table to database

        Arguments:
            name {String} -- table name
            data {DataFrame} -- table data
            index {bool} -- add index to table (default: {True})
        """
        data.to_sql(name, con=self.conn, if_exists='replace', index=index)
        if TRACING:
            print(f'table: {name} added')

    def add_geotable(self, name, geodata, index=True):
        """Add a geopandas table to database

        Arguments:
            name {String} -- table name
            data {GeoDataFrame} -- table data
            index {bool} -- add index to table (default: {True})
        """
        _geo = geodata.copy(deep=True)
        _geo['geometry'] = _geo['geometry'].apply(lambda x: x.wkb_hex)
        _geo.to_sql(name, con=self.conn, if_exists='replace', index=index)
        if TRACING:
            print(f'geotable: {name} added')

    def get_table(self, name, index_col=None, parse_dates=None, columns=None):
        """Return dataframe from database

        Arguments:
            name {String} -- table name
            columns {list} -- column name(s) to read from table (default: {None})
            index_col {String or list} -- column name(s) (default: {None})
            parse_dates {list or dict} -- column name(s) (default: {None})

        Returns:
            {DataFrame} -- table data
        """
        if columns:
            _cols = ', '.join(columns)
        else:
            _cols = '*'

        _query = pd.read_sql_query(sql=f"select {_cols} from {name};",
                                   con=self.conn,
                                   index_col=index_col,
                                   parse_dates=parse_dates)
        if TRACING:
            print(f'table: {name} returned')
        return pd.DataFrame(_query)

    def get_geotable(self, name, index_col=None, parse_dates=None, columns=None):
        """Return geodataframe from database

        Arguments:
            name {String} -- table name
            columns {list} -- column name(s) to read from table (default: {None})
            index_col {String or list} -- column name(s) (default: {None})
            parse_dates {list or dict} -- column name(s) (default: {None})

        Returns:
            {GeoDataFrame} -- table data
        """
        _geo = self.get_table(name, index_col=index_col,
                              parse_dates=parse_dates, columns=columns)
        _geo['geometry'] = _geo['geometry'].apply(lambda x: wkb.loads(x, hex=True))
        if TRACING:
            print(f'geotable: {name} returned')
        return gpd.GeoDataFrame(_geo)

    def close(self):
        """Close database connection
        """
        self.conn.close()
        if TRACING:
            print('database connection closed')
