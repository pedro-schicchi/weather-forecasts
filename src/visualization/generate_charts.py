import os
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import cartopy.crs as ccrs
import cartopy.feature as cf


width = 8.5
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Montserrat']
plt.rcParams['figure.figsize'] = width, width*0.76

def get_projections(proj_name, central_lon=-96, central_lat=39.0):
    try:
        projections = {
            'mercator':ccrs.Mercator(),
            'lambert':ccrs.LambertConformal(central_longitude=central_lon, central_latitude=central_lat),
        }
        return projections[proj_name]
    except:
        print('Selected did not work, using standard "mercator"')
        return ccrs.Mercator()

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
    
    def plot_map(self, region, step_range, variable, title=None, cbar_label=None):
        # support variables
        get_keys = lambda dic, k_list: [dic[k] for k in k_list]    
        map_params = self.region_params.loc[region]
        min_lon, max_lon, min_lat, max_lat, central_lon, central_lat = get_keys(map_params, ['min_lon','max_lon','min_lat','max_lat','avg_lon', 'avg_lat'])
        proj_name = map_params['projection']
        states = map_params['states']
        
        # specify map projection and coordinate refference system (crs)
        proj = get_projections(proj_name, central_lon, central_lat)
        crs = ccrs.PlateCarree()
        
        # creates axes object having specific projection
        fig, ax = plt.subplots(subplot_kw=dict(projection=proj), dpi=500)
        ax.set_extent([min_lon, max_lon, min_lat, max_lat], crs=crs)
        
        # prepare dataset
        # to_plot = self.raw_data.sel(x=slice(min_lon-20, max_lon+20), y=slice(min_lat-20, max_lat+20))
        if proj_name=='lambert':
            to_plot = self.raw_data.sel(x=slice(min_lon-20, max_lon+20), y=slice(min_lat-5, max_lat+5))
        else:
            to_plot = self.raw_data.sel(x=slice(min_lon, max_lon), y=slice(min_lat, max_lat))
        to_plot, date_start, date_end = self.aggregate_steps(to_plot, step_range)
        
        # To plot borders and coastlines, we can use cartopy feature
        ax.add_feature(cf.COASTLINE.with_scale('50m'), lw=0.75)
        ax.add_feature(cf.BORDERS.with_scale('50m'), lw=0.75)
        if states:
            ax.add_feature(cf.STATES.with_scale('50m'), lw=0.25)
        
        # # Draw gridlines in degrees over Mercator map
        # gl = ax.gridlines(crs=crs, draw_labels=True, linewidth=.5, color='gray', alpha=0.5, linestyle='--')
        # gl.top_labels = False
        # gl.bottom_labels = True
        # gl.right_labels = False
        # gl.left_labels = True   
        
        # Actually plots the dataset on top of the projection
        to_plot[variable].plot.contourf(
            ax=ax,
            transform=crs,
            extend='both',
            levels=15,
            robust=True,
            cmap=self.custom_cmap(variable),
            cbar_kwargs={'location':'right', 'label':cbar_label},
        )
        
        # returns the figure
        plt.title(title)
        return fig