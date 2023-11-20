# %%
import os
import numpy as np
import xarray as xr
# import warnings

# warnings.filterwarnings('ignore')

# %%
# def get_reference_values(attribute, ref_dir, data_ds):
#     # helper variables
#     variables = {1:'t2m', 2:'tp'}
    
#     # get raw dataset
#     doy = list(data_ds.date.dt.dayofyear.values)
#     fns = [os.path.join(ref_dir,f'era5_1990-2020_doy_{d}_{attribute}.tif') for d in doy]
#     step = xr.DataArray(np.arange(1,len(doy)+1)*np.timedelta64(1, 'D'), dims='step')
#     ds = xr.open_mfdataset(fns, combine='nested', concat_dim=step).load()
    
#     # rename
#     ds_list = []
#     for k,v in variables.items():
#         temp = ds.sel(band=k).rename({'band_data':v}).drop('band')
#         ds_list = ds_list + [temp]
#     ds = xr.merge(ds_list)
    
#     # final adjustments
#     ds = ds.assign(tp = ds.tp*1000)
#     ds = ds.interp_like(data_ds).mean(dim='step')
    
#     return ds
# %%
class ProcessGefs:
    def __init__(self, attribute, fcst_fn=None, ltm_fn=None):
        self.attribute = attribute
        self.fcst_data = xr.open_dataset(fcst_fn)
        self.ltm_data = xr.open_dataarray(ltm_fn)

    def to_imperial(self, da):
        if self.attribute == 'precip':
            da = da / 25.4 
        else:
            da = (da * 9/5) + 32

        return da

    def get_array(self, step_range, anomaly=False, unit_system='metric'):
        # average out data within the selected timespan
        fcst = self.fcst_data[self.attribute].sel(step=step_range)
        ltm = self.ltm_data.sel(time=list(fcst.doy.values))
        ltm = ltm.interp_like(fcst)

        # data is naturally in metric, if imperial then it is converted
        if unit_system == 'imperial':
            fcst = self.to_imperial(fcst)
            ltm = self.to_imperial(ltm)

        # if anomaly, then subtract long term mean
        if anomaly:
            fcst = fcst.mean('step') - ltm.mean('time')

        # mean across time
        else:
            fcst = fcst.mean('step')

        return fcst

# %% old
# def calculate_anomalies(self, ref_dir, inplace=True):
#     ds = self.data
    
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
#     if inplace: self.data = ds
#     return ds

# def save(self, out_dir):
#     dest_file =  os.path.join(out_dir,'gefs_fcst.nc')
#     self.data.to_netcdf(dest_file)


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
    RAW_DIR = os.path.join(BASE_DIR, '..', '..', 'data', 'raw')
    
    # inputs
    attribute = 'tavg'

    # process data
    noaa = ProcessGefs(
        attribute=attribute,
        fcst_fn=os.path.join(RAW_DIR, 'gefs', 'gefs_fcst.nc'),
        ltm_fn=os.path.join(RAW_DIR, 'cpc_ltm', f'{attribute}_ltm.nc'),
        
    )
    fcst = noaa.get_array(step_range=slice('1 days', '14 days'), anomaly=True)

    