import os
from abc import ABC, abstractmethod
import warnings
import cftime

import pandas as pd
import xarray as xr
from urllib.request import urlretrieve

# warnings.filterwarnings('ignore')


class GetCpc(ABC):
    def __init__(self, attribute, year, out_dir, use_cftime=False):
        self.attribute = attribute
        self.year = year
        self.use_cftime = use_cftime

        self.prefix = 'precip' if self.attribute == 'precip' else 'temp'
        self.out_dir = out_dir
        self.out_file = os.path.join(out_dir, f'{self.attribute}_{self.year}.nc')

    @abstractmethod
    def download_url(self):
        pass
    
    @abstractmethod
    def date2doy(self, date_array):
        pass

    def get_data(self, delete_raw=False):
        # average temperature is the only 'construcetd' attribute, therefore the process is different
        if self.attribute == 'tavg':
            print('opening minimum and maximum')
            tmin = xr.open_dataarray(os.path.join(self.out_dir, f'tmin_{self.year}.nc'))
            tmax = xr.open_dataarray(os.path.join(self.out_dir, f'tmax_{self.year}.nc'))

            print('calculating average')
            ds = (tmin + tmax) / 2

        else:
            print('downloading data')
            raw_path = self.download_data(self.out_dir)

            print('processing raw data')
            ds = xr.load_dataset(raw_path, use_cftime=self.use_cftime)
            ds = self.preprocess_data(ds)

            if delete_raw:
                print('deleting raw data')
                os.remove(raw_path)

        print('saving processed data')
        ds.to_netcdf(self.out_file)

        return ds

    def download_data(self, out_dir):
        url = self.download_url()
        out_path = os.path.join(out_dir, f'temp_{self.attribute}_{self.year}.nc')
        urlretrieve(url, out_path)
        return out_path

    def preprocess_data(self, ds):
        # convert numbers - dates to doy and longitude
        ds = ds.assign_coords(time=self.date2doy(ds.time))
        ds['lon'] = (ds['lon'] + 180) % 360 - 180

        # filter single series
        ds = ds[self.attribute].sortby(['lat','lon'])

        return ds

class GetCpcYear(GetCpc):
    def __init__(self, attribute, year, out_dir):
        super().__init__(
            attribute=attribute,
            year=year,
            out_dir=out_dir,
            use_cftime=False
        )

    def download_url(self):
        return f'https://downloads.psl.noaa.gov/Datasets/cpc_global_{self.prefix}/{self.attribute}.{self.year}.nc'

    def date2doy(self, date_array):
        return pd.to_datetime(date_array).day_of_year

class GetCpcLtm(GetCpc):
    def __init__(self, attribute, out_dir) -> None:
        super().__init__(
            attribute=attribute,
            year='ltm',
            out_dir=out_dir,
            use_cftime=True
        )

    def download_url(self):
        # calculate last closed decade based on current year
        current_year = pd.Timestamp.today().year
        decade = f'{current_year // 10 * 10 - 29}-{current_year // 10 * 10}'
        return f'https://downloads.psl.noaa.gov/Datasets/cpc_global_{self.prefix}/{self.attribute}.day.ltm.{decade}.nc'

    def date2doy(self, date_array):
        return cftime.date2num(date_array, 'days since 1-1-1') + 1

# %%
if __name__ == '__main__':
    # inputs
    current_year = pd.Timestamp.today().year
    reload_ltm = False

    # define directories
    BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
    RAW_DIR = os.path.join(BASE_DIR, 'data', 'raw')
    
    # get curr year data
    # for att in ['precip', 'tmin', 'tmax', 'tavg']:
    for att in ['tmin', 'tmax', 'tavg']:
        print(f'GETTING {att.upper()}:')

        if reload_ltm:
            ltm = GetCpcLtm(attribute=att, out_dir=os.path.join(RAW_DIR, 'cpc_ltm'))
            ds = ltm.get_data(delete_raw=True)

        curr = GetCpcYear(attribute=att, year=current_year, out_dir=os.path.join(RAW_DIR, 'cpc'))
        curr.get_data(delete_raw=True)
# %%
