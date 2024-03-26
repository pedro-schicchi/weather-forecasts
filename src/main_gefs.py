# %% standard libraries
import os
from time import perf_counter

# third party libraries
import pandas as pd

# custom libraries
from data.get_config import GetConfig
from data.gefs_get import GetGefs
from features.gefs_process import ProcessGefs
from visualization.generate_maps import WeatherMap
from visualization.generate_reports import GenerateReports

# %% main
if __name__ == '__main__':
    # globals
    today = pd.Timestamp.today()

    # standard paramaters to print
    run_hour = 0
    languages_to_plot = ['en', 'pt']

    # set directory
    BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
    REF_DIR = os.path.join(BASE_DIR, 'references')
    RAW_DIR = os.path.join(BASE_DIR, 'data', 'raw')
    REP_DIR = os.path.join(BASE_DIR, 'reports')
    FIG_DIR = os.path.join(BASE_DIR, 'reports', 'figures', 'gefs')

    # configurations
    config_file = os.path.join(REF_DIR, 'configurations.xlsx')
    regions = GetConfig(config_file, 'regions')
    colors = GetConfig(config_file, 'colors')
    images = GetConfig(config_file, 'images')
    
    print('getting new data')
    start = perf_counter()
    query = GetGefs(
        start_date=today,
        number_of_days=15,
        run_cycle=run_hour)
    query.get_data(os.path.join(RAW_DIR, 'gefs'), delete_raw=True)
    print(f'\n--time passed = {perf_counter()-start:.2f}')

    # loop through images and plot
    for i, row in images.data.iterrows():
        # get data from row
        start = perf_counter()
        region = row.region
        attribute = row.attribute
        variable = 'precip' if attribute == 'precip' else 'temp'
        anomaly = row.anomaly
        unit =  row.unit
        figname = row.filename
        cbar_label = row.label
        step_range = slice(f'{row.start} days', f'{row.end} days')

        print('\r plotting data', end='')

        # processing data
        noaa = ProcessGefs(
            attribute=attribute,
            fcst_fn=os.path.join(RAW_DIR, 'gefs', 'gefs_fcst.nc'),
            ltm_fn=os.path.join(RAW_DIR, 'cpc_ltm', f'{attribute}_ltm.nc'),
        )
        fcst = noaa.get_array(
            step_range=step_range,
            anomaly=anomaly,
            unit_system=unit
        )
        
        # plot map
        maps = WeatherMap(data_array=fcst, attribute=attribute, anomaly=anomaly)
        fig = maps.plot_map(
            region_meta=regions.get_region_meta(region),
            cmap=colors.custom_cmap(variable, anomaly),
            cbar_label=cbar_label, 
            eliminate_strange = False
        )
        fig.savefig(os.path.join(FIG_DIR, figname), bbox_inches='tight')

        # feedback to user
        print(f'--time passed = {perf_counter()-start:.2f}')
   
    # updates ppt files
    print('updating ppt')
    for lang in languages_to_plot:
        ppt_file = os.path.join(REP_DIR, f'weather_report_{lang}.pptx')
        
        # updates figures in the ppt file placeholders
        genrep = GenerateReports(ppt_file, images.data[images.data['language'] == lang], fig_dir=FIG_DIR)
        genrep.update_ppt()