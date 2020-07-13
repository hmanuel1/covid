
"""Refresh data

"""
import enum

from nytimes import download_nytimes
from fldem import download_fldem
from arima import predict
from clf import classify
from database import DataBase
from wrangler import maps_to_database
from utilities import ElapsedMilliseconds
from sql import (
    VACUUM,
    REINDEX
)

class Status(enum.Enum):
    """Refresh Data Enumeration

    Arguments:
        enum {Enum} -- refresh status
    """
    idle = 1
    busy = 2
    done = 3

class  RefreshData:
    """Refresh database with enable/disable control

    """
    def __init__(self):
        self.enable = False
        self.status = Status.idle
        self.time = ElapsedMilliseconds()

    def data(self):
        """ Refresh database covid19 data

        """
        if self.enable and self.status == Status.idle:
            self.time.restart()
            print('data refresh started.')
            self.enable = False
            self.status = Status.busy
            refresh_data()
            self.status = Status.idle
        else:
            print('ERROR: refresh is disabled.')

    def maps(self):
        """ Refresh database map data

        """
        if self.enable and self.status == Status.idle:
            print('map refresh started.')
            self.time.restart()
            self.enable = False
            self.status = Status.busy
            refresh_maps()
            self.status = Status.done
        else:
            print('ERROR: refresh is disabled.')

    def duration(self):
        """Return duration in minutes of refresh

        Returns:
            float -- duration in minutes
        """
        return round(self.time.elapsed()/(60*1000), 1)



def refresh_data():
    """
        Refresh covid-19 data used by this app
    """
    print('downloading nytimes data...', end='')
    download_nytimes()
    # print('done.\ndownloading fldem data...', end='')
    # download_fldem()
    # print('done.\nclassifying with fldem data...', end='')
    # classify()
    print('done.\npredicting with nytimes data...', end='')
    predict()
    print('done.')

    _db = DataBase()
    _db.update(VACUUM)
    _db.update(REINDEX)
    _db.close()


def refresh_maps():
    """
        Refresh database maps
        it needs geopandas install
    """
    print('refreshing database maps...')
    maps_to_database()
    print('done.')

    _db = DataBase()
    _db.update(VACUUM)
    _db.update(REINDEX)
    _db.close()

if __name__ == "__main__":
    refresh_data()
