import os
from datetime import date, timedelta
import pandas as pd

from data.get_config import GetConfig
from data.cpc_get import GetCpcLtm, GetCpcYear
from features.cpc_process import ProcessCpc
from visualization.generate_maps import WeatherMap

if __name__ == '__main__':
    # define directories
    BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
    REF_DIR = os.path.join(BASE_DIR, 'references')
    RAW_DIR = os.path.join(BASE_DIR, 'data', 'raw')
    FIG_DIR = os.path.join(BASE_DIR, 'reports', 'figures', 'cpc')

    # globals
    today = date.today()
    current_year = today.year
    end_date = today - timedelta(2)

    # inputs
    region = 'south_america'
    attribute = 'precip'
    anomaly = True
    reload_ltm = False
    reload_curr = False
    periods = 14
    
    # input-dependent variables
    # variable = 'tp' if attribute == 'precip' else 't2m'
    doys = pd.date_range(end=end_date, periods=14, freq='D').day_of_year.to_list()
    figname = f'{region}_{attribute}_{periods}_{"anom" if anomaly else ""}.png'
    
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
    da = cpc.get_array(doys, anomaly=anomaly)

    print('creating the weather map')
    maps = WeatherMap(
        data_array=da,
        attribute=attribute,
        anomaly=anomaly
    )
    fig = maps.plot_map(
        region_meta=regions.get_region_meta(region),
        cmap=colors.custom_cmap(attribute, anomaly)
    )
    fig.savefig(os.path.join(FIG_DIR, figname), bbox_inches='tight')