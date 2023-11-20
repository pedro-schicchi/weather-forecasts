import os
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import cartopy.crs as ccrs
import cartopy.feature as cf


width = 8.5
# plt.rcParams['font.family'] = 'sans-serif'
# plt.rcParams['font.sans-serif'] = ['Montserrat']
# plt.rcParams['figure.figsize'] = width, width*0.76

var_label = {
    'precip':'Precipitation',
    'temp':'Temperature',
}

anom_label = {
    True:'Anomaly',
    False:'',
}

unit_label = {
    ('precip', 'metric'):'(mm/d)',
    ('precip', 'imperial'):'(in/d)',
    ('temp', 'metric'):'°C',
    ('temp', 'imperial'):'°F',
}

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
    def __init__(self, data_array, attribute, anomaly=False, unit_system='metric'):
        self.data_array = data_array
        self.attribute = attribute
        self.anomaly = anomaly
        self.variable = 'precip' if attribute == 'precip' else 'temp'
        self.extend = 'max' if self.variable == 'precip' and not anomaly else 'both'
        
    def plot_map(self, region_meta, cmap=None, cbar_label=None, title=None, grid=False):
        
        # support variables
        min_lon, max_lon, min_lat, max_lat = region_meta[['min_lon','max_lon','min_lat','max_lat']].to_list()
        central_lon, central_lat = region_meta[['avg_lon', 'avg_lat']].to_list()
        proj_name = region_meta['projection']
        states = region_meta['states']
        if not cbar_label:
            cbar_label = f'{var_label[self.variable]} {anom_label[self.anomaly]} {unit_label[(self.variable, self.unit_system)]}'
        
        # specify map projection and coordinate refference system (crs)
        proj = get_projections(proj_name, central_lon, central_lat)
        crs = ccrs.PlateCarree()
        
        # creates axes object having specific projection
        fig, ax = plt.subplots(subplot_kw=dict(projection=proj), dpi=500)
        ax.set_extent([min_lon, max_lon, min_lat, max_lat], crs=crs)
        
        # prepare dataset
        if proj_name=='lambert':
            to_plot = self.data_array.sel(lon=slice(min_lon-20, max_lon+20), lat=slice(min_lat-5, max_lat+5))
        else:
            to_plot = self.data_array.sel(lon=slice(min_lon, max_lon), lat=slice(min_lat, max_lat))
        
        # To plot borders and coastlines, we can use cartopy feature
        ax.add_feature(cf.COASTLINE.with_scale('50m'), lw=0.75)
        ax.add_feature(cf.BORDERS.with_scale('50m'), lw=0.75)
        if states:
            ax.add_feature(cf.STATES.with_scale('50m'), lw=0.25)
        
        # # Draw gridlines in degrees over Mercator map
        if grid:
            gl = ax.gridlines(crs=crs, draw_labels=True, linewidth=.5, color='gray', alpha=0.5, linestyle='--')
            gl.top_labels = False
            gl.bottom_labels = True
            gl.right_labels = False
            gl.left_labels = True   
        
        # Actually plots the dataset on top of the projection
        to_plot.plot.contourf(
            ax=ax,
            transform=crs,
            extend=self.extend,
            levels=15,
            robust=True,
            cmap=cmap,
            cbar_kwargs={'location':'right', 'label':cbar_label},
        )
        
        # returns the figure
        plt.title(title)
        return fig