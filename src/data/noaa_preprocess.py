import os
import numpy as np
import xarray as xr

class PreProcessNOAA:
    def __init__(self):
        pass
    
    def get_filenames(self, data_dir):
        filenames = [os.path.join(data_dir,fn) for fn in os.listdir(data_dir) if '.idx' not in fn]
        filenames.sort()
        return filenames
    
    def load(self, data_dir, n_days=None, inplace=True):
        # if a number of days was given, transform into number of files by multiplying it by 4
        filenames = self.get_filenames(data_dir)
        if n_days: filenames = filenames[:(n_days * 4)]
        # read data
        ds = xr.open_mfdataset(filenames, combine='nested', concat_dim='step', engine='cfgrib')
        ds.load()
        
        if inplace: self.data = ds
        return ds
    
    def preprocess(self, inplace=True):
        ds = self.data
        # transform_coords
        ds = ds.drop(labels=['heightAboveGround','surface'])
        ds = ds.rename({'longitude':'x','latitude':'y'})
        
        # group in days by mean - steps come in 6h by standard
        ds = ds.assign(step = (np.ceil(ds.step.values / np.timedelta64(1, 'D'))).astype('timedelta64[D]'))
        ds = ds.groupby('step').mean()
        
        # precipititation (tp) is issued in 6h accumulated figures
        # since was aggregated in days by 'mean', to get 24h acc we multiply by 4
        ds = ds.assign(tp = ds.tp * 4)
        
        # add date dimension
        ds = ds.assign_coords(date=ds.time + ds.step)
        ds = ds.assign_coords(doy=ds.date.dt.dayofyear)
        
        # convert lons
        ds = ds.assign(x=(ds.x + 180) % 360 - 180)
        ds = ds.sortby(['x','y'])
        
        if inplace: self.data = ds
        return ds

    def save(self, out_dir):
        dest_file =  os.path.join(out_dir,'gefs_fcst.nc')
        self.data.to_netcdf(dest_file)



if __name__ == '__main__':
    # set directory
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, '..', '..', 'data', 'raw', 'gefs')
    OUTPUT_DIR = os.path.join(BASE_DIR, '..', '..', 'data', 'interim')
    
    # process data
    noaa = PreProcessNOAA()
    noaa.load(DATA_DIR)
    noaa.preprocess()
    noaa.save(OUTPUT_DIR)
    
    # # test
    # ds = xr.open_dataset(os.path.join(OUTPUT_DIR,'gefs_fcst.nc'))
    # print(ds)