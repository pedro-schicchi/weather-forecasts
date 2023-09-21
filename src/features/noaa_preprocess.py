import os
import numpy as np
import xarray as xr
import warnings

warnings.filterwarnings('ignore')

def get_reference_values(attribute, ref_dir, data_ds):
    # helper variables
    variables = {1:'t2m', 2:'tp'}
    
    # get raw dataset
    doy = list(data_ds.date.dt.dayofyear.values)
    fns = [os.path.join(ref_dir,f'era5_1990-2020_doy_{d}_{attribute}.tif') for d in doy]
    step = xr.DataArray(np.arange(1,len(doy)+1)*np.timedelta64(1, 'D'), dims='step')
    ds = xr.open_mfdataset(fns, combine='nested', concat_dim=step).load()
    
    # rename
    ds_list = []
    for k,v in variables.items():
        temp = ds.sel(band=k).rename({'band_data':v}).drop('band')
        ds_list = ds_list + [temp]
    ds = xr.merge(ds_list)
    
    # final adjustments
    ds = ds.assign(tp = ds.tp*1000)
    ds = ds.interp_like(data_ds).mean(dim='step')
    
    return ds

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

    def calculate_anomalies(self, ref_dir, inplace=True):
        ds = self.data
        
        # reference values
        mean = get_reference_values('mean', ref_dir, ds)
        std = get_reference_values('std', ref_dir, ds)
        
        # anomaly
        anom = ds[['t2m','tp']] - mean
        anom = anom.rename({'tp':'tp_anom','t2m':'t2m_anom'})
        
        # percentage anomaly
        anom_norm = (ds[['t2m','tp']] / mean) * 100
        anom_norm = anom_norm.rename({'tp':'tp_anom_perc','t2m':'t2m_anom_perc'})
        
        # # final dataset
        ds = xr.merge([ds, anom, anom_norm])
        if inplace: self.data = ds
        return ds

    def save(self, out_dir):
        dest_file =  os.path.join(out_dir,'gefs_fcst.nc')
        self.data.to_netcdf(dest_file)


# def calculate_anomalies(ds, ref_dir, inplace=True):
#     # reference values
#     mean = get_reference_values('mean', ref_dir, ds)
#     std = get_reference_values('std', ref_dir, ds)
    
#     # anomaly
#     anom = ds[['t2m','tp']] - mean
#     anom = anom.rename({'tp':'tp_anom','t2m':'t2m_anom'})
    
#     # percentage anomaly
#     anom_norm = (ds[['t2m','tp']] / mean) * 100
#     anom_norm = anom_norm.rename({'tp':'tp_anom_perc','t2m':'t2m_anom_perc'})
    
#     # # final dataset
#     ds = xr.merge([ds, anom, anom_norm])
#     # if inplace: self.data = ds
#     return ds

# %%

if __name__ == '__main__':
    # set directory
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    REF_DIR = os.path.join(BASE_DIR, '..', '..', 'references', 'era5_ref')
    DATA_DIR = os.path.join(BASE_DIR, '..', '..', 'data', 'raw', 'gefs')
    OUTPUT_DIR = os.path.join(BASE_DIR, '..', '..', 'data', 'interim')
    
    # process data
    noaa = PreProcessNOAA()
    noaa.load(DATA_DIR)
    noaa.preprocess()
    mean = noaa.calculate_anomalies(REF_DIR)
    noaa.save(OUTPUT_DIR)  
    # 
    # %%
    
    # mean = calculate_anomalies(noaa.data, REF_DIR)
    