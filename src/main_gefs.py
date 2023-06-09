# standard libraries
import os
# from time import perf_counter

# third party libraries
# import numpy as np
import pandas as pd
# 

# custom libraries
from utils import delete_all_files
from data.noaa_query import QueryNOAA
from data.noaa_preprocess import PreProcessNOAA
    
if __name__ == '__main__':
    # inputs
    today = pd.Timestamp.today()
    run_hour = 0 # 0, 6, 12, 18

    # set directory
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, '..', 'data', 'raw', 'gefs')
    OUTPUT_DIR = os.path.join(BASE_DIR, '..', 'data', 'processed', 'gefs')
    
    # delete old runs - for space
    delete_all_files(DATA_DIR)
    
    # download new run
    print('getting new data')
    query = QueryNOAA(start_date=today, run_cycle=run_hour)
    query.get_forecast(number_of_days=15, out_dir=DATA_DIR)
    
    # preprocess data
    print('processing data')
    noaa = PreProcessNOAA()
    noaa.load(DATA_DIR)
    noaa.preprocess()
    noaa.save(OUTPUT_DIR)
    
    