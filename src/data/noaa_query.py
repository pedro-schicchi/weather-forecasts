import os
import urllib.request
import urllib.parse

class QueryNOAA:
    def __init__(self, start_date, run_cycle, variables=['APCP','TMP']):
        self.date = start_date
        self.run_cycle = run_cycle
        self.variables = variables
        
    def create_url(self, valid_time):
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
    
    def get_file(self, valid_time, out_dir):
        # url and filename
        url = self.create_url(valid_time)
        fn = os.path.join(out_dir,f'gefs_{valid_time}.grb2')
        # download
        urllib.request.urlretrieve(url, fn)
        return fn

    def get_forecast(self, number_of_days, out_dir):
        for valid_time in range(6, number_of_days*24 + 1, 6):
            print(f'\r--{valid_time} hours', end='')
            self.get_file(valid_time, out_dir)
  
# actual
# https://nomads.ncep.noaa.gov/cgi-bin/filter_gefs_atmos_0p50a.pl?dir=/gefs.20230609/00/atmos/pgrb2ap5&file=geavg.t00z.pgrb2a.0p50.f006&var_APCP=on&all_lev=on
# code
# https://nomads.ncep.noaa.gov/cgi-bin/filter_gefs_atmos_0p50a.pl?dir=/gefs.20230609/00/atmos/pgrb2ap5&file=geavg.t00z.pgrb2a.0p50.f006&var_APCP=on