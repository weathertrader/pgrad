
'''
name: plot_stn_map.py 
purpose: plot maps of stations used by pgrad.io 
author: Craig Smith, craig.matthew.smith@gmail.com
usage: python src/plot_stn_map.py 
repo: https://github.com/weathertrader/pgrad
'''
 
import os
import sys
import pandas as pd 
import numpy as np
#import requests 
#from datetime import datetime as dt
#from datetime import timedelta as td
#import time 
#import np 
#import argparse 
#import xarray
#from netCDF4 import Dataset 

import matplotlib
#matplotlib.use('Agg') 
import matplotlib.pyplot as plt
#from matplotlib.dates import drange, DateFormatter
#from matplotlib.ticker import MultipleLocator 

import matplotlib.ticker as mticker
import cartopy.crs as ccrs
import cartopy.io.shapereader as shpreader
from cartopy.io import shapereader
from cartopy.mpl.gridliner import LATITUDE_FORMATTER, LONGITUDE_FORMATTER
import cartopy.feature as cfeature
from cartopy.feature import ShapelyFeature
from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter

# os.getcwd()
os.chdir(os.path.join(os.getenv('HOME'), 'pgrad'))
     
sys.path.append(os.path.join(os.getcwd(), 'src'))
from pgrad import read_stn_metadata_from_csv

# read station locations
use_stn = 'all'
print_stn_info = False
#read_stn_metadata_type = 'csv' # 'db' or 'csv'
project_name = 'pgrad'
stn_metadata_file_name = os.path.join(os.environ['HOME'], project_name, 'station_list_'+project_name+'.csv') 
(dict_stn_metadata) = read_stn_metadata_from_csv(stn_metadata_file_name, use_stn, print_stn_info)
    
#pd.read_csv(stn_metadata_file_name,index_col=0)
#n_stn = len(dict_stn_metadata['stn_id'])

size_scatter = 20           
colors_s = ['k', 'r', 'b', 'g', 'c', 'm', 'y',
            'k', 'r', 'b', 'g', 'c', 'm', 'y']
plot_counties = False
country_provinces = cfeature.NaturalEarthFeature(category='cultural',
                                                 name='admin_0_boundary_lines_land',
                                                 scale='50m',
                                                 facecolor='none')
states_provinces = cfeature.NaturalEarthFeature(category='cultural',
                                                name='admin_1_states_provinces_lines',
                                                scale='50m',
                                                facecolor='none')

width_roads = 1.0
[hgt_min, hgt_max, hgt_int] = [-500, 13000, 1000]        
# ca and nv
#[lon_min, lon_max, lon_int] = [-125.0, -114.0, 2.0]
#[lat_min, lat_max, lat_int] = [  32.0,   42.2, 1.0]
[lon_min, lon_max, lon_int] = [-126.0, -112.0, 2.0]
[lat_min, lat_max, lat_int] = [  31.0,   45.0, 1.0]


fig = plt.figure(num=110,figsize=(10, 10)) # 10x5, 10x6, 10x10 
plt.clf()
ax = plt.axes(projection=ccrs.PlateCarree())
#ax = plt.axes(projection=ccrs.LambertConformal())
ax.set_extent([lon_min, lon_max, lat_min, lat_max])        
ax.set_xticks(np.arange(lon_min, lon_max, lon_int), crs=ccrs.PlateCarree())
ax.set_yticks(np.arange(lat_min, lat_max, lat_int), crs=ccrs.PlateCarree())
lon_formatter = LongitudeFormatter(number_format='.1f',dateline_direction_label=True)
lat_formatter = LatitudeFormatter(number_format='.1f')                 
#ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=False, linewidth=0.5, color='gray', alpha=1.0, linestyle='-')

#ax.add_feature(states_provinces, edgecolor='k', linewidth=2.0)
#ax.add_feature(country_provinces, edgecolor='k', linewidth=2.0)
ax.coastlines(resolution='10m', color='k', linewidth=2.0) # 10m, 50m, 110m

shape_file_name = os.path.join('data', 'shp_files', 'tl_2013_us_primaryroads')
shape_feature = ShapelyFeature(shapereader.Reader(shape_file_name).geometries(), ccrs.PlateCarree())
ax.add_feature(shape_feature, edgecolor='g', linewidth=width_roads, facecolor='none')

shape_file_name = os.path.join('data', 'shp_files', 'tl_2013_06_prisecroads')
shape_feature = ShapelyFeature(shapereader.Reader(shape_file_name).geometries(), ccrs.PlateCarree())
ax.add_feature(shape_feature, edgecolor='g', linewidth=width_roads, facecolor='none')

if (plot_counties):
    shape_file_name = os.path.join(dir_shp, 'counties', 'tl_2014_us_county')
    shape_feature = ShapelyFeature(shapereader.Reader(shape_file_name).geometries(), ccrs.PlateCarree())
    ax.add_feature(shape_feature, edgecolor='m', linewidth=1.0, facecolor='none')

size_marker = 10 # 10
# plot sfc obs
alpha_level = 0.5 # 0.3
s = 358
#for s in range(0, n_stn):
for s in range(0, dict_stn_metadata['n_stn']):
    marker_edge_color = 'k'
    marker_edge_width = 1.0 # 0.5 # 1.0
    ax.plot(dict_stn_metadata['stn_lon'][s], dict_stn_metadata['stn_lat'][s], marker='o', markersize=size_marker, markerfacecolor='r', markeredgecolor=marker_edge_color, markeredgewidth=marker_edge_width, alpha=alpha_level, transform=ccrs.PlateCarree())
    ax.text(dict_stn_metadata['stn_lon'][s], dict_stn_metadata['stn_lat'][s], dict_stn_metadata['stn_id'][s][1:], color = 'k', fontsize=10, fontweight='bold', ha='left', transform=ccrs.PlateCarree())                    
  
plt.xlabel('longitude', fontsize=12, labelpad=10) # 10 is too small, 20 
plt.ylabel('latitude',  fontsize=12, labelpad=10) # 30 is too small, 60 
plt.title('station map  ' ,fontsize=12, loc='left', weight = 'bold')   
plt.show()
plt.tight_layout()        
filename = 'stn_map.png'
plot_name = os.path.join('top_events', filename) 
dpi_level = 400 # 400        
#plt.savefig(plot_name)
plt.savefig(plot_name, dpi=dpi_level) 
#fig.clf()
#plt.close()        








