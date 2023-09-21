import cartopy
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER

def plotMap():
    regions = {
        'north_america':[-120, -70, 15, 60],
        'europe':[ -15, 45, 32, 68],
        'south_america':[-85, -30, -40, 13],
        'southeast_asia':[90,135,-20,20],
        'china':[77,128,15,54],
        'australia':[112,155,-44,-8],
        'india':[63,95,5,36],
    }
    
    min_lon, max_lon, min_lat, max_lat = regions['india']
    
    # proj = ccrs.Mercator(central_longitude=-94.5, min_latitude=15, max_latitude=50)
    # proj = ccrs.LambertAzimuthalEqualArea()
    # proj = ccrs.LambertConformal(central_longitude=(min_lon+max_lon)/2, central_latitude=(min_lat+max_lat)/2)
    proj = ccrs.Mercator()

    fig, ax = plt.subplots(subplot_kw=dict(projection=proj), figsize=(12,12))
    ax.set_extent([min_lon, max_lon, min_lat, max_lat], crs=ccrs.PlateCarree())


    # ax.set_extent([ -15, 45, 32, 68], crs=ccrs.PlateCarree())
    # ax.set_extent([-120, -70, 15, 60], crs=ccrs.PlateCarree())
    # ax.set_extent([-85, -30, -40, 13], crs=ccrs.PlateCarree())

    # ax.add_feature(cfeature.LAND, facecolor='0.3')
    ax.add_feature(cfeature.LAKES, alpha=0.9)  
    ax.add_feature(cfeature.COASTLINE, zorder=10)
    ax.add_feature(cfeature.BORDERS, zorder=10)
    # ax.add_feature(cfeature.STATES, zorder=10)

    # states_provinces = cfeature.NaturalEarthFeature(
    #         category='cultural', 
    #         name='admin_1_states_provinces_lines',
    #         scale='50m',
    #         facecolor='none'
    #     )
    # ax.add_feature(states_provinces, edgecolor='black', zorder=10)   

    # gl = ax.gridlines(crs=ccrs.PlateCarree(), linewidth=0.5, color='black', alpha=0.5, linestyle='--', draw_labels=True)
    # gl.top_labels = False
    # gl.bottom_labels = True
    # gl.right_labels = False
    # gl.left_labels = True    
    
    # gl.xlines = True
    # gl.xlocator = mticker.FixedLocator([120, 140, 160, 180, -160, -140, -120])
    # gl.ylocator = mticker.FixedLocator([0, 20, 40, 60])
    # gl.xformatter = LONGITUDE_FORMATTER
    # gl.yformatter = LATITUDE_FORMATTER
    # gl.xlabel_style = {'color': 'red', 'weight': 'bold'}
    
plotMap()