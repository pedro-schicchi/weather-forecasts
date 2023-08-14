import os
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cf

plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Montserrat']

def get_region_bounds(region):
    # [min_lon, max_lon, min_lat, max_lat]
    region_dict = {
        'global':None,
        'europe':(-20,45,34,60),
        'conus_mex':(-126,-63,15,50),
        'conus':(-126,-63,25,50),
        'northAm':(-135,-60,15,55),
        'southAm':(-85,-30,-40,13),
        'southeastAsia':(90,135,-20,20),   
        'china':(72,137,15,50),
        }
    return region_dict[region]

def slice_region(ds, region):
    [min_lon, max_lon, min_lat, max_lat] = get_region_bounds(region)
    return ds.sel(x=slice(min_lon,max_lon), y=slice(min_lat,max_lat))

class WeatherMap:
    def __init__(self, source='gefs'):
        self.source = source
        
    
    def load_data(self, data_dir, inplace=True):
        filename = os.path.join(data_dir,f'{self.source}_fcst.nc')
        ds = xr.load_dataset(filename)
        
        if inplace: self.raw_data = ds
        return ds
    
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
    
    def plot_map(self, region, step_range, variable, metric=True): #
        
        
        # prepare dataset
        to_plot = slice_region(self.raw_data, region)
        to_plot, date_start, date_end = self.aggregate_steps(to_plot, step_range)
        
        # support variables
        [min_lon, max_lon, min_lat, max_lat] = get_region_bounds(region)
    #     label, unit, color_scheme = get_variable_infos(variable, metric)

        # Specify Map Projection and CRS (Coordinate Refference System)
        # Mercator: has very large distortion at high latitudes, cannot fully reach the polar regions.
        projection = ccrs.Mercator()
        crs = ccrs.PlateCarree()
        
        # Now we will create axes object having specific projection
        plt.figure(figsize=(14.5,9), dpi=500) #
        ax = plt.axes(projection=projection, frameon=True)
        
        # Draw gridlines in degrees over Mercator map
        gl = ax.gridlines(crs=crs, draw_labels=True, linewidth=.6, color='gray', alpha=0.5, linestyle='-.')
        gl.xlabel_style = {'size' : 7}
        gl.ylabel_style = {'size' : 7}
        
        # To plot borders and coastlines, we can use cartopy feature
        ax.add_feature(cf.COASTLINE.with_scale('50m'), lw=0.5)
        ax.add_feature(cf.BORDERS.with_scale('50m'), lw=0.5)
        ax.add_feature(cf.STATES.with_scale('50m'), lw=0.3)
        
        # Now, we will specify extent of our map in minimum/maximum longitude/latitude
        ax.set_extent([min_lon, max_lon, min_lat, max_lat], crs=crs)

        # Actually plots the dataset on top of the projection
        cbar_kwargs = {
            'orientation':'vertical',
            'shrink':0.75,
            # 'pad' : 0.05,
            # 'aspect':40,
            # 'label':f'{label} ({unit})'
        }
        to_plot[variable].plot.contourf(
            ax=ax,
            transform=crs,
            extend='both',
            # vmin=min_max_levels[0],
            # vmax=min_max_levels[1],
            levels=15, # min_max_levels[2]
            robust=True,
            # cmap=custom_cmap(color_scheme),
            cbar_kwargs=cbar_kwargs,
        )
        
    #     plt.title(None)
    #     if date_end != None:
    #         plt.title(f'NOAA GEFS {label} - {date_start} to {date_end}')
    #     else:
    #         plt.title(f'NOAA GEFS {label} - {date_start}')
        plt.show()
    #     plt.savefig(f'{img_folder}{region}_{variable}_{step_range[0]}_to_{step_range[1]}.png', bbox_inches='tight')