import os
import urllib.request
import urllib.parse
import numpy as np
import pandas as pd
import xarray as xr

def delete_temp_files(folder):
    generator = (fn for fn in os.listdir(folder) if 'temp_' in fn)
    for fn in generator:
        os.remove(os.path.join(folder,fn))

class GetGefs:
    def __init__(self, start_date, number_of_days, run_cycle, variables=['APCP','TMP']):
        self.date = start_date
        self.number_of_days = number_of_days
        self.steps = range(6, number_of_days*24 + 1, 6)
        self.run_cycle = run_cycle
        self.variables = variables

    def get_data(self, out_dir, out_file='gefs_fcst.nc', delete_raw=False):
        print('downloading individual 6h forecasts')
        filenames = [self.download_forecast(valid_time, out_dir) for valid_time in self.steps]

        print('\rprocessing raw data')
        ds = xr.open_mfdataset(filenames, combine='nested', concat_dim='step', engine='cfgrib')
        ds = self.preprocess_data(ds)

        print('saving processed data')
        ds.to_netcdf(os.path.join(out_dir, out_file))

        if delete_raw:
            print('deleting raw data')
            delete_temp_files(out_dir)

        return ds

    def download_url(self, valid_time):
        # transform inputs into the desired format 
        date = self.date.strftime('%Y%m%d')
        run_cycle = str(self.run_cycle).zfill(2)
        valid_time = str(valid_time).zfill(3)
        # directory and file - dependent on date, run_cycle and valid time
        api_params = {
            'dir':f'/gefs.{date}/{run_cycle}/atmos/pgrb2ap5',
            'file':f'geavg.t{run_cycle}z.pgrb2a.0p50.f{valid_time}',
            'lev_surface':'on', 
            'lev_2_m_above_ground':'on'
        }
        # add variables to get from file
        api_params = api_params | {f'var_{var}':'on' for var in self.variables}        
        # return url
        url = 'https://nomads.ncep.noaa.gov/cgi-bin/filter_gefs_atmos_0p50a.pl?' + urllib.parse.urlencode(api_params)
        return url
    
    def download_forecast(self, valid_time, out_dir):
        print(f'\r--{valid_time} hours', end='')
        
        # url and filename
        url = self.download_url(valid_time)
        fn = os.path.join(out_dir,f'temp_gefs_{valid_time}.grb2')
        
        # download
        urllib.request.urlretrieve(url, fn)

        return fn

    def preprocess_data(self, ds):
        # transform_coords
        ds = ds.drop(labels=['heightAboveGround','surface'])
        ds = ds.rename({
            'longitude':'lon',
            'latitude':'lat',
            'tp':'precip',
            't2m':'tavg'
        })
        
        # group in days by mean - steps come in 6h by standard
        ds = ds.assign(step = (np.ceil(ds.step.values / np.timedelta64(1, 'D'))).astype('timedelta64[D]').astype('timedelta64[ns]'))
        ds = ds.groupby('step').mean()
        
        # change temperature to celsius
        ds = ds.assign(tavg = ds.tavg -273.15)

        # precipititation is issued in 6h accumulated figures, to get 24h acc we multiply by 4
        ds = ds.assign(precip = ds.precip * 4)
        
        # add date dimension
        ds = ds.assign_coords(date=ds.time + ds.step)
        ds = ds.assign_coords(doy=ds.date.dt.dayofyear)

        # convert lons
        ds = ds.assign(lon=(ds.lon + 180) % 360 - 180)

        # filter series and sort
        ds = ds.sortby(['lon','lat'])
        
        return ds

# 
if __name__ == '__main__':

    BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
    RAW_DIR = os.path.join(BASE_DIR, 'data', 'raw', 'gefs')
    INT_DIR = os.path.join(BASE_DIR, 'data', 'interim', 'gefs')

    today = pd.Timestamp.today()
    gefs = GetGefs(
        start_date=today,
        number_of_days=15,
        run_cycle=0,
    )
    ds = gefs.get_data(RAW_DIR, delete_raw=True)