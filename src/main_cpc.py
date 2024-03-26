# %% setup

import os
from datetime import date, timedelta
import numpy as np
import pandas as pd
import xarray as xr

from data.get_config import GetConfig
from data.cpc_get import GetCpcLtm, GetCpcYear
from features.cpc_process import ProcessCpc
from visualization.generate_maps import WeatherMap

# %%

if __name__ == '__main__':
    # define directories
    BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
    REF_DIR = os.path.join(BASE_DIR, 'references')
    RAW_DIR = os.path.join(BASE_DIR, 'data', 'raw')
    FIG_DIR = os.path.join(BASE_DIR, 'reports', 'figures', 'cpc')

    # %% globals
    
    today = date.today()
    
    
    # end_date = today - timedelta(2)
    end_date = pd.Timestamp('2024-02-21')
    
    
    current_year = end_date.year
    periods = end_date.day

    # %% inputs
    region = 'south_america'
    attribute = 'tavg'
    anomaly = True
    reload_ltm = False
    reload_curr = False
    elim_anom = False
    
    # input-dependent variables
    variable = 'precip' if attribute == 'precip' else 'temp'
    doys = pd.date_range(end=end_date, periods=periods, freq='D').day_of_year.to_list()
    figname = f'{region}_{attribute}_{end_date.strftime("%Y-%m-%d")}_{periods}{"_anom" if anomaly else ""}.png'
    
    # configurations
    regions = GetConfig(os.path.join(REF_DIR, 'configurations.xlsx'), 'regions')
    colors = GetConfig(os.path.join(REF_DIR, 'configurations.xlsx'), 'colors')

    print('reloading long term mean data')
    ltm = GetCpcLtm(
        attribute,
        out_dir=os.path.join(RAW_DIR, 'cpc_ltm')
    )
    if reload_ltm: ltm.get_data(delete_raw=True)
    
    print('reloading curr year data')
    curr = GetCpcYear(
        attribute,
        current_year,
        out_dir=os.path.join(RAW_DIR, 'cpc')
    )
    if reload_curr: curr.get_data(delete_raw=True)

    print('creating a data array')
    cpc = ProcessCpc(
        attribute=attribute,
        curr_fn=curr.out_file,
        ltm_fn=ltm.out_file
    )
    da = cpc.get_array(doys, anomaly=anomaly, imperial=False)
    
    # %%
    print('creating the weather map')
    

    # if anomaly:
    #     levels=np.arange(-5, 6, 1),
    # elif attribute != 'precip':
    #     levels=None
    # else:
    #     levels=np.arange(0, 13, 2)
    
    maps = WeatherMap(
        data_array=da,
        attribute=attribute,
        anomaly=anomaly,
        unit_system='metric'
    )
    fig = maps.plot_map(
        region_meta=regions.get_region_meta(region),
        cmap=colors.custom_cmap(variable, anomaly),
        levels=np.arange(-5, 6, 1),
        eliminate_strange=elim_anom
    )
    fig.savefig(os.path.join(FIG_DIR, figname), bbox_inches='tight')