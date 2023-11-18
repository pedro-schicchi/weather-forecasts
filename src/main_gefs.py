# %% standard libraries
import os
from time import perf_counter
import warnings


# third party libraries
import pandas as pd

# custom libraries
from utils import delete_all_files
from data.noaa_query import QueryNOAA
from features.noaa_preprocess import PreProcessNOAA
from visualization.generate_charts import WeatherMap
from visualization.generate_reports import GenerateReports

warnings.filterwarnings('ignore')

# %% main
if __name__ == '__main__':
    # globals
    start = perf_counter()
    today = pd.Timestamp.today()
    
    # inputs
    # run_hour = int(input('Forecast run hour (0, 6, 12, 18): ') or '0')
    # vars_to_plot = input('Variables to plot (tp, t2m, tp_anom, t2m_anom): ').split() or ['tp_anom', 't2m_anom']
    # regions_to_plot = input(f'Regions to plot ({", ".join(region_params.index)}): ').split() or ['north_america', 'europe', 'south_america', 'southeast_asia']
    
    # standard paramaters to print
    run_hour = 0
    vars_to_plot = ['tp', 'tp_anom', 't2m', 't2m_anom']
    regions_to_plot = ['north_america','central_america', 'south_america',  'europe', 'india', 'southeast_asia', 'australia']
    languages_to_plot = ['en', 'pt']
    # vars_to_plot = ['tp_anom', 't2m_anom']
    # regions_to_plot = ['north_america']
    # languages_to_plot = ['en']

    # set directory
    BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
    REF_DIR = os.path.join(BASE_DIR, 'references')
    RAW_DIR = os.path.join(BASE_DIR, 'data', 'raw', 'gefs')
    INT_DIR = os.path.join(BASE_DIR, 'data', 'interim', 'gefs')
    REP_DIR = os.path.join(BASE_DIR, 'reports')
    FIG_DIR = os.path.join(BASE_DIR, 'reports', 'figures', 'gefs_fcst')
    
    # manual parameters are taken from an excel file, as it is easier for the user to change
    with pd.ExcelFile(os.path.join(REF_DIR, 'manual_inputs.xlsx')) as xl:
        region_params = xl.parse(sheet_name='regions', index_col=0)
        color_codes = xl.parse(sheet_name='colors', index_col=0)
        image_files = xl.parse(sheet_name='images')
        labels = xl.parse(sheet_name='labels', index_col=[0,1])
        xl.close()
    
    # %% download new run
    print('getting new data')
    delete_all_files(RAW_DIR)
    query = QueryNOAA(start_date=today, run_cycle=run_hour)
    query.get_forecast(number_of_days=15, out_dir=RAW_DIR)
    print(f'\n--time passed = {perf_counter()-start:.2f}')
    
    # %% preprocess data
    print('processing data')
    noaa = PreProcessNOAA()
    ds = noaa.load(RAW_DIR)
    ds = noaa.preprocess()
    ds = noaa.calculate_anomalies(os.path.join(REF_DIR, 'era5_ref') )
    noaa.save(INT_DIR)
    print(f'--time passed = {perf_counter()-start:.2f}')
    
    # %% plot map
    print('plotting map')
    maps = WeatherMap(data_dir=INT_DIR, region_params=region_params, color_codes=color_codes)            
            
    for i, row in image_files.iterrows():   
        # 
        print(row.filename)
        
        # plot maps
        step = (f'{row.start} days', f'{row.end} days')
        fig = maps.plot_map(region=row.region,step_range=step, variable=row.variable, cbar_label=row.label, unit_system=row.unit)
        fig.savefig(os.path.join(FIG_DIR,row.filename), bbox_inches='tight')

    print(f'--time passed = {perf_counter()-start:.2f}')
    
    # # updates ppt files
    # print('updating ppt')
    # for lang in languages_to_plot:
    #     ppt_file = os.path.join(REP_DIR, f'weather_report_{lang}.pptx')
        
    #     # updates figures in the ppt file placeholders
    #     genrep = GenerateReports(ppt_file, image_files[image_files['language'] == lang], fig_dir=FIG_DIR)
    #     genrep.update_ppt()