import os
import pandas as pd
import xarray as xr
from datetime import timedelta

class ProcessCpc:
    def __init__(self, attribute, curr_fn=None, ltm_fn=None) -> None:
        # 
        self.attribute = attribute
        # self.year = year
        # self.directory = directory

        # open data
        self.ltm_data = xr.open_dataarray(ltm_fn)
        self.curr_data = xr.open_dataarray(curr_fn)

    def to_imperial(self, da):
        if self.attribute == 'precip':
            da = da / 25.4 
        else:
            da = (da * 9/5) + 32

        return da

    def get_array(self, doy_range, anomaly=False, imperial=False):
        # average out data within the selected timespan
        curr = self.curr_data.sel(time=doy_range)
        ltm = self.ltm_data.sel(time=doy_range)

        # data is naturally in metric, if imperial then it is converted
        if imperial:
            curr = self.to_imperial(curr)
            ltm = self.to_imperial(ltm)

        # if anomaly, then subtract long term mean
        if anomaly:
            curr = curr - ltm

        # mean across time
        curr = curr.mean('time')

        return curr
    
if __name__ == '__main__':
    # define directories
    BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
    RAW_DIR = os.path.join(BASE_DIR, 'data', 'raw')
    # INT_DIR = os.path.join(BASE_DIR, 'data', 'raw', 'cpc_global')

    # inputs
    attribute = 'tavg'
    today = pd.Timestamp.today().date() - timedelta(1)

    curr_fn = os.path.join(RAW_DIR, 'cpc', f'{attribute}_{today.year}.nc')
    ltm_fn = os.path.join(RAW_DIR, 'cpc_ltm', f'{attribute}_ltm.nc')
    doys = pd.date_range(end=today, periods=14, freq='D').day_of_year.to_list()

    # test
    cpc = ProcessCpc(attribute=attribute, curr_fn=curr_fn, ltm_fn=ltm_fn)
    tavg = cpc.get_array(doys)
    tavg_anom = cpc.get_array(doys, anomaly=True)