import os
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from mpl_toolkits.axes_grid1 import make_axes_locatable
import cartopy.crs as ccrs
import cartopy.feature as cf

plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Montserrat']

# def get_region_bounds(region):
#     # [min_lon, max_lon, min_lat, max_lat]
#     region_dict = {
#         'global':None,
#         'europe':(-20,45,34,60),
#         'conus_mex':(-126,-63,15,50),
#         'conus':(-126,-63,25,50),
#         'northAm':(-135,-60,15,55),
#         'southAm':(-85,-30,-40,13),
#         'southeastAsia':(90,135,-20,20),   
#         'china':(72,137,15,50),
#         }
#     return region_dict[region]


class WeatherMap:
    def __init__(self, data_dir, region_params, color_codes, source='gefs', inplace=True):
        # dataset file
        filename = os.path.join(data_dir,f'{source}_fcst.nc')
        
        # hex2rgb in 0-1 format, instead of the normal 0-255
        color_codes['rgb'] = color_codes['hex'].apply(lambda h: tuple(int(h[i:i+2], 16)/255 for i in (0, 2, 4)))
        
        self.source = source
        self.region_params = region_params
        self.color_codes = color_codes
        self.raw_data = xr.load_dataset(filename)
    
    def custom_cmap(self, color_scheme):
        # transform given color scheme into rgb tuples
        if isinstance(color_scheme, str):
            color_lists = {
                'tp':['white', 'yellow', 'green', 'blue'],
                't2m':['red', 'grey', 'blue'],
                'tp_anom':['orange', 'white',  'dark_blue'],
                't2m_anom':['blue', 'white', 'red',],
            }
            rgb_tuples = [self.color_codes.loc[c_str, 'rgb'] for c_str in color_lists[color_scheme]]
        
        elif isinstance(color_scheme, (list, tuple)):
            rgb_tuples = [self.color_codes.loc[c_str, 'rgb'] for c_str in color_scheme]
        
        else:
            raise ValueError('Unknown color scheme')
        
        return LinearSegmentedColormap.from_list('mycmap', rgb_tuples, N=256)
    
    # def slice_region(ds, region):
    #     [min_lon, max_lon, min_lat, max_lat] = get_region_bounds(region)
    #     return ds.sel(x=slice(min_lon,max_lon), y=slice(min_lat,max_lat))
    
    def aggregate_steps(self, ds, step_range):
        """Takes an xarray dataset with forecasts and a tuple of numpy.timedelta that is consistent with the
        dataset's 'step' coordinate unit. 
        The dates within the min/max range will be selected and aggregated through the mean

        Args:
            ds (xr.Dataset): the dataset that will be sliced and aggregated 
            step_range (tuple of np.timedelta): the min/max dates to aggregate

        Returns:
            ds_agg: the resulting dataset after the aggregation
            date_start: pd.Timestamp for the map legend
            date_end: pd.Timestamp for the map legend
        """
        
        # select desired range dates
        ds_agg = ds.sel(step=slice(step_range[0], step_range[1])).copy()
        
        try:
            date_start = pd.Timestamp(ds_agg.date.values.min()).strftime('%d-%b')
            date_end = pd.Timestamp(ds_agg.date.values.max()).strftime('%d-%b')
        except:
            date_start = pd.Timestamp(2022,step_range[0],1).strftime('%B')
            date_end = None
        
        # aggregate dataset
        ds_agg = ds_agg.mean('step')
        
        return ds_agg, date_start, date_end
    
    def plot_map(self, region, step_range, variable, title=None):
        # support variables
        rp = self.region_params.loc[region]
        
        # prepare dataset
        to_plot = self.raw_data.sel(x=slice(rp['min_lon'], rp['max_lon']), y=slice(rp['min_lat'], rp['max_lat'])) #slice_region(self.raw_data, region)
        to_plot, date_start, date_end = self.aggregate_steps(to_plot, step_range)
        
        # support variables
        [min_lon, max_lon, min_lat, max_lat] = self.get_region_bounds(region)
    #     label, unit, color_scheme = get_variable_infos(variable, metric)

        # Specify Map Projection and CRS (Coordinate Refference System)
        # Mercator: has very large distortion at high latitudes, cannot fully reach the polar regions.
        proj = ccrs.Mercator()
        crs = ccrs.PlateCarree()
        
        # Now we will create axes object having specific projection
        # fig = plt.figure(dpi=500) #figsize=(14.5,9), 
        # ax = plt.axes(projection=projection, frameon=True)
        fig, ax = plt.subbplots(subplot_kw=dict(projection=proj), dpi=500)
       
        # Draw gridlines in degrees over Mercator map
        gl = ax.gridlines(crs=crs, draw_labels=True, linewidth=.5, color='gray', alpha=0.5, linestyle='--')
        # gl.xlabel_style = {'size':5}
        # gl.ylabel_style = {'size':5}
        
        # To plot borders and coastlines, we can use cartopy feature
        ax.add_feature(cf.COASTLINE.with_scale('50m'), lw=0.5)
        ax.add_feature(cf.BORDERS.with_scale('50m'), lw=0.5)
        # ax.add_feature(cf.STATES.with_scale('50m'), lw=0.3)
        
        # Now, we will specify extent of our map in minimum/maximum longitude/latitude
        ax.set_extent([min_lon, max_lon, min_lat, max_lat], crs=crs)

        # Actually plots the dataset on top of the projection
        cbar_kwargs = {
            # 'cax':cax
            # 'location':'bottom',
            # 'location':'right',
            'fraction':0.15,
            'pad':0.05,
            # 'shrink':0.85,
            # 'pad' : 0.05,
            'aspect':30,
            # 'label':f'{label} ({unit})'
        }
        to_plot[variable].plot.contourf(
            ax=ax,
            transform=crs,
            extend='both',
            levels=15,
            robust=True,
            cmap=self.custom_cmap(variable),
            cbar_kwargs=cbar_kwargs,
        )
        
        plt.title(title)
        return fig
    
    
    
if __name__ == '__main__':
    # set directory
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    REF_DIR = os.path.join(BASE_DIR, '..', '..', 'references') #, 'era5_ref'
    RAW_DIR = os.path.join(BASE_DIR, '..', '..', 'data', 'raw', 'gefs')
    INT_DIR = os.path.join(BASE_DIR, '..', '..', 'data', 'interim', 'gefs')
    
    
    
    
    # maps = WeatherMap(INT_DIR)
    
    
    