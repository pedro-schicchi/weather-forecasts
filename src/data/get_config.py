import os
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

class GetConfig:
    def __init__(self, filename, data) -> None:
        idx_col = {
            'regions':0,
            'colors':0,
            'images':None,
            'labels':[0,1]
        }

        # get dataframe
        xl = pd.ExcelFile(filename)
        self.data = xl.parse(sheet_name=data, index_col=idx_col[data])
        xl.close()

    def get_region_meta(self, region_name):
        return self.data.loc[region_name]
    
    def custom_cmap(self, variable:str, anomaly:bool):
        color_codes = self.data.copy()

        # hex2rgb in 0-1 format, instead of the normal 0-255
        color_codes['rgb'] = color_codes['hex'].apply(lambda h: tuple(int(h[i:i+2], 16)/255 for i in (0, 2, 4)))

        # transform given color scheme into rgb tuples
        try:
            color_lists = {
                ('precip', False):['grey', 'white', 'light_green', 'dark_green', 'light_blue', 'blue', 'purple'],
                ('temp', False):['blue', 'light_blue', 'white', 'orange', 'red'],
                ('precip', True):['orange', 'white', 'dark_blue'],
                ('temp', True):['blue', 'white', 'red'],
            }
            rgb_tuples = [color_codes.loc[c_str, 'rgb'] for c_str in color_lists[(variable, anomaly)]]
        
        except:
            raise ValueError('Unknown color scheme')
        
        return LinearSegmentedColormap.from_list('mycmap', rgb_tuples, N=256)

# # manual parameters are taken from an excel file, as it is easier for the user to change
# with pd.ExcelFile(os.path.join(REF_DIR, 'manual_inputs.xlsx')) as xl:
#     region_params = xl.parse(sheet_name='regions', index_col=0)
#     color_codes = xl.parse(sheet_name='colors', index_col=0)
#     image_files = xl.parse(sheet_name='images')
#     labels = xl.parse(sheet_name='labels', index_col=[0,1])
#     xl.close()