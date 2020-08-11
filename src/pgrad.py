
'''
name: pgrad.py 
purpose: process and analyze pressure gradient forcing from NWP models 
author: Craig Smith, craig.matthew.smith@gmail.com
usage: ./src/run.sh n  where n is the number of batteries to analyze [1-5]
repo: https://github.com/weathertrader/battery_charge
'''

# side project plan 
# 1 d
# local -> s3
#     download 
#     process 
#     log 
#     plots

# stations - done
#      grab station locations 
#      write stn to csv
#      read stn from csv 


# download data - 2 hr
# 6    adjust curl filter to correct variables 
# 9b   works for gfs, nam, and hrrr

# calc_grad - 2 hr
#     read/update pgrad csv 
#     update forecasts avail csv 

# plotting - 4 hr
#     plot static local
#     plot s3

# stn obs operational - 1d 
#     download local
#     download static

# station observations historical
#     download
#     tables of top historical events 



# website - 4 d
#     front end js static
#     front end dynamic 

# environment, requirements.txt - 2h

# code -> lambda, operationalize - 1d  
# url deploy, infra, recovery - 2d 



import os
import sys
import csv
import argparse 
import pandas as pd
import numpy as np
import xarray as xr
# import cfgrib
from datetime import datetime as dt 
from datetime import timedelta as td 
import glob
import requests
import subprocess

import matplotlib
import matplotlib.pyplot as plt
# plotting from cli
matplotlib.use('Agg') 

import logging 
#import xarray
#from netCDF4 import Dataset 

#os.getcwd()
#os.chdir('/home/csmith/battery_charge')
#n_files = 5

###############################################################################    
def create_log_file(log_name_full_file_path, dt_start_utc, time_zone_label):
    if not (os.path.isdir(os.path.dirname(log_name_full_file_path))):
        #os.mkdir(os.path.dirname(log_name_full_file_path))
        os.system('mkdir -p '+os.path.dirname(log_name_full_file_path))    
    formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(module)s - %(message)s') 
    logger    = logging.getLogger(log_name_full_file_path)
    handler   = logging.FileHandler(log_name_full_file_path) 
    formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter) 
    logger.addHandler(handler) 
    logger.setLevel(logging.INFO) # INFO, DEBUG,INFO,WARNING,ERROR,CRITICAL    
    print      ('###############################################################################') 
    logger.info('###############################################################################') 
    print      ('instantiate_logger log_name is %s ' % (log_name_full_file_path))     
    logger.info('instantiate_logger log_name is %s ' % (log_name_full_file_path))     
    print      ('instantiate_logger at %s %s ' % (dt_start_lt.strftime('%Y-%m-%d_%H-%M'), time_zone_label))
    logger.info('instantiate_logger at %s %s ' % (dt_start_lt.strftime('%Y-%m-%d_%H-%M'), time_zone_label))            
    return logger


###############################################################################
def close_logger(logger, process_name, dt_start_lt, utc_conversion, time_zone_label):
    dt_end_lt = dt.utcnow() - td(hours=utc_conversion)
    time_delta_minutes = (dt_start_lt - dt_end_lt).seconds/60.0
    print      ('total_time %s %05.1f minutes, %s - %s [%s]  ' % (process_name, time_delta_minutes, dt_start_lt.strftime('%Y-%m-%d_%H-%M'), dt_end_lt.strftime('%Y-%m-%d_%H-%M'), time_zone_label))
    logger.info('total_time %s %05.1f minutes, %s - %s [%s]  ' % (process_name, time_delta_minutes, dt_start_lt.strftime('%Y-%m-%d_%H-%M'), dt_end_lt.strftime('%Y-%m-%d_%H-%M'), time_zone_label))
    print      ('###############################################################################') 
    logger.info('###############################################################################') 
  
    
###############################################################################    
def define_daylight_savings_or_not(dt_temp_utc):    
    #yy_temp = dt.strftime(dt_temp_utc,'%Y')
    #yy_temp = int(yy_temp) 
    yy_temp = dt_temp_utc.year
    if   (yy_temp == 2018):
        dt_dst_start = dt(2018,  3, 11, 10) 
        dt_dst_end   = dt(2018, 11,  4, 10) 
    elif (yy_temp == 2019):
        dt_dst_start = dt(2019,  3, 10, 10)  
        dt_dst_end   = dt(2019, 11,  3, 10)   
    elif (yy_temp == 2020):
        dt_dst_start = dt(2020,  3,  8, 10)
        dt_dst_end   = dt(2020, 11,  1, 10)
    elif (yy_temp == 2021):
        dt_dst_start = dt(2021,  3, 14, 10)
        dt_dst_end   = dt(2021, 11,  7, 10)
    elif (yy_temp == 2022):
        dt_dst_start = dt(2022,  3, 13, 10)
        dt_dst_end   = dt(2022, 11,  6, 10)
    elif (yy_temp == 2023):
        dt_dst_start = dt(2023,  3, 12, 10)
        dt_dst_end   = dt(2024, 11,  5, 10)
    elif (yy_temp == 2024):
        dt_dst_start = dt(2024,  3, 10, 10)
        dt_dst_end   = dt(2024, 11,  3, 10)
    if ((dt_temp_utc >= dt_dst_start) and (dt_temp_utc <= dt_dst_end)):
        utc_conversion, time_zone_label = 7, 'PDT'
    else:
        utc_conversion, time_zone_label = 8, 'PST'
    return utc_conversion, time_zone_label

###############################################################################
def define_expected_forecast_available_from_wallclock(logger, model_name, update_frequency_hrs):
    '''get expected most recent forecast based on wall clock time  '''
    
    dt_utc = dt.utcnow()    

    #if ((model_name == 'hrrr') or (model_name == 'nam')):
    # HRRR
    # 20:52 - 21:30 20Z avail 
    # 21:52 - 22:21 21Z avail 
    # 22:55 - 23:XX 22Z avail 
    if   (update_frequency_hrs == 1):
        if (dt_utc.minute < 21):
            dt_init_expected = dt_utc - td(hours=2)
        else: 
            dt_init_expected = dt_utc - td(hours=1)
        dt_init_expected = dt(dt_init_expected.year, dt_init_expected.month, dt_init_expected.day, dt_init_expected.hour, 0, 0)
    elif (update_frequency_hrs == 6):
        dt_init_expected = dt_utc - td(hours=2)
        if    (dt_init_expected.hour < 6):
            hour_to_use = 0
        elif ((dt_init_expected.hour >=  6) & (dt_init_expected.hour < 12)):
            hour_to_use = 6
        elif ((dt_init_expected.hour >= 12) & (dt_init_expected.hour < 18)):
            hour_to_use = 12
        elif (dt_init_expected.hour >= 18):
            hour_to_use = 18
        dt_init_expected = dt(dt_init_expected.year, dt_init_expected.month, dt_init_expected.day, hour_to_use, 0, 0)
    elif (update_frequency_hrs == 12):
        dt_init_expected = dt_utc - td(hours=2)
        if    (dt_init_expected.hour < 12):
            hour_to_use = 0
        else:
            hour_to_use = 12
        dt_init_expected = dt(dt_init_expected.year, dt_init_expected.month, dt_init_expected.day, hour_to_use, 0, 0)
    #else: 
    #    print      ('  ERROR: get_expected_most_recent_forecast not defined for %s ' % (model_name))
    #    logger.info('  ERROR: get_expected_most_recent_forecast not defined for %s ' % (model_name))

    print      ('  expecting %s %s Z to be available ' % (model_name, dt_init_expected.strftime('%Y-%m-%d %H')))
    logger.info('  expecting %s %s Z to be available ' % (model_name, dt_init_expected.strftime('%Y-%m-%d %H')))

    return dt_init_expected


###############################################################################
def download_data(model_name, dt_init, forecast_horizon_hr, bucket_name):

    hr = 0
    file_exists_on_remote = True
    while hr < forecast_horizon_hr and file_exists_on_remote:
        print      ('    processing hr %s of %s ' % (hr, forecast_horizon_hr))
        logger.info('    processing hr %s of %s ' % (hr, forecast_horizon_hr))    
        dir_init_temp = dt_init.strftime('%Y-%m-%d')
        file_name = model_name+'_'+dt_init.strftime('%Y-%m-%d_%H')+'_t_'+str(hr).rjust(2,'0')+'.grib2'
        dir_name_ingest    = os.path.join('data', 'ingest',    dir_init_temp)
        dir_name_processed = os.path.join('data', 'processed', dir_init_temp)
        file_name_ingest    = os.path.join(dir_name_ingest, file_name)
        file_name_processed = os.path.join(dir_name_processed, file_name)
        print      ('    file_ingest %s, file_processed %s ' % (file_name_ingest, file_name_processed))
        logger.info('    file_ingest %s, file_processed %s ' % (file_name_ingest, file_name_processed))
        # mkdir if doesnt exist
        if not os.path.isdir(dir_name_ingest):
            os.system('mkdir -p '+dir_name_ingest)
        if not os.path.isdir(dir_name_processed):
            os.system('mkdir -p '+dir_name_processed)
        #if   (model_name == 'hrrr'):        
        #elif (model_name == 'nam'):        

        if not (os.path.isfile(file_name_ingest) or os.path.isfile(file_name_processed)):
            # check if exists on remote            
            if   (model_name == 'hrrr'):
                base_url = 'https://nomads.ncep.noaa.gov/pub/data/nccf/com/hrrr/prod/hrrr.'
                url_folder_str = dt_init.strftime('%Y')+dt_init.strftime('%m')+dt_init.strftime('%d')
                file_name_remote = model_name+'.t'+dt_init.strftime('%H')+'z.wrfsfcf'+str(hr).rjust(2,'0')+'.grib2'
                url_temp = base_url+url_folder_str+'/conus/'+file_name_remote
            elif (model_name == 'nam'):
                base_url = 'https://nomads.ncep.noaa.gov/pub/data/nccf/com/nam/prod/nam.'
                url_folder_str = dt_init.strftime('%Y')+dt_init.strftime('%m')+dt_init.strftime('%d')
                file_name_remote = model_name+'.t'+dt_init.strftime('%H')+'z.conusnest.hiresf'+str(hr).rjust(2,'0')+'.tm00.grib2'
                url_temp = base_url+url_folder_str+'/'+file_name_remote
            elif (model_name == 'gfs'):
                base_url = 'https://nomads.ncep.noaa.gov/pub/data/nccf/com/'+model_name+'/prod/'
                url_folder_str1 = model_name+'.'+dt_init.strftime('%Y%m%d')
                url_folder_str2 = dt_init.strftime('%H')                
                file_name_remote = model_name+'.t'+dt_init.strftime('%H')+'z.pgrb2.0p25.f'+str(hr).zfill(3)
                url_temp = base_url+url_folder_str1+'/'+url_folder_str2+'/'+file_name_remote
            print      ('    url_temp is %s ' % (url_temp))
            logger.info('    url_temp is %s ' % (url_temp))
  
            #response = requests.head(url_temp+'no')
            response = requests.head(url_temp)
            #response.headers
            if response.status_code != 200: # 404 not found
                file_exists_on_remote = False
                print      ('    file does not exist on remote')
                logger.info('    file does not exist on remote')
                break
            else:             
                print      ('    file exists on remote')
                logger.info('    file exists on remote')
  
                if   (model_name == 'hrrr'):
                    # curl_command = 'curl "https://nomads.ncep.noaa.gov/cgi-bin/filter_hrrr_2d.pl?file='+file_name_remote+'&lev_10_m_above_ground=on&lev_2_m_above_ground=on&lev_surface=on&var_HGT=on&var_PRES=on&var_RH=on&var_TMP=on&var_UGRD=on&var_VGRD=on&var_APCP=on&var_DPT=on&var_FRICV=on&var_GUST=on&var_LAND=on&var_WIND=on&var_HGT=on&var_PRES=on&var_RH=on&var_TMP=on&var_UGRD=on&var_VGRD=on&subregion=&leftlon=-160&rightlon=-110&toplat=50&bottomlat=25&dir=%2Fhrrr.'+url_folder_str+'%2Fconus" -o '+file_name_ingest
                    # curl_command = 'curl "https://nomads.ncep.noaa.gov/cgi-bin/filter_hrrr_2d.pl?file='+file_name_remote+'&lev_2_m_above_ground=on&lev_mean_sea_level=on&lev_surface=on&var_HGT=on&var_MSLMA=on&var_PRES=on&var_APCP=on&var_UGRD=on&var_VGRD=on&subregion=&leftlon=-160&rightlon=-110&toplat=50&bottomlat=25&dir=%2Fhrrr.'+url_folder_str+'%2Fconus" -o '+file_name_ingest
                    # curl_command = 'curl "https://nomads.ncep.noaa.gov/cgi-bin/filter_hrrr_2d.pl?file='+file_name_remote+'&lev_mean_sea_level=on&lev_surface=on&var_HGT=on&var_MSLMA=on&var_PRES=on&var_UGRD=on&var_VGRD=on&subregion=&leftlon=-160&rightlon=-110&toplat=50&bottomlat=25&dir=%2Fhrrr.'+url_folder_str+'%2Fconus" -o '+file_name_ingest
                    curl_command = 'curl "https://nomads.ncep.noaa.gov/cgi-bin/filter_hrrr_2d.pl?file='+file_name_remote+'&lev_mean_sea_level=on&lev_surface=on&var_HGT=on&var_MSLMA=on&var_PRES=on&subregion=&leftlon=-160&rightlon=-110&toplat=50&bottomlat=25&dir=%2Fhrrr.'+url_folder_str+'%2Fconus" -o '+file_name_ingest
                
                elif (model_name == 'nam'):
                    # nam   
                    # curl_command = 'curl "https://nomads.ncep.noaa.gov/cgi-bin/filter_nam.pl?file=nam.t00z.awphys00.tm00.grib2&lev_10_m_above_ground=on&lev_mean_sea_level=on&lev_surface=on&var_PRES=on&var_PRMSL=on&var_UGRD=on&var_VGRD=on&subregion=&leftlon=-160&rightlon=-110&toplat=50&bottomlat=25&dir=%2Fnam.20200810" -o '+file_name_ingest
                    # curl_command = 'curl "https://nomads.ncep.noaa.gov/cgi-bin/filter_nam.pl?file=nam.t00z.awphys00.tm00.grib2&lev_10_m_above_ground=on&lev_mean_sea_level=on&lev_surface=on&var_PRES=on&var_PRMSL=on&var_UGRD=on&var_VGRD=on&subregion=&leftlon=-160&rightlon=-110&toplat=50&bottomlat=25&dir=%2Fnam.'+url_folder_str+'" -o '+file_name_ingest
                    # use this one
                    curl_command = 'curl "https://nomads.ncep.noaa.gov/cgi-bin/filter_nam.pl?file=nam.t'+dt_init.strftime('%H')+'z.awphys'+str(hr).zfill(2)+'.tm00.grib2&lev_mean_sea_level=on&lev_surface=on&var_PRES=on&var_PRMSL=on&subregion=&leftlon=-160&rightlon=-110&toplat=50&bottomlat=25&dir=%2Fnam.'+url_folder_str+'" -o '+file_name_ingest
                    # nam conus
                    # https://nomads.ncep.noaa.gov/cgi-bin/filter_nam.pl?file=nam.t00z.awphys00.tm00.grib2&lev_mean_sea_level=on&lev_surface=on&var_PRES=on&var_PRMSL=on&leftlon=0&rightlon=360&toplat=90&bottomlat=-90&dir=%2Fnam.20200811
                    # nam hires nest 
                    # https://nomads.ncep.noaa.gov/cgi-bin/filter_nam_conusnest.pl?file=nam.t00z.conusnest.hiresf00.tm00.grib2&lev_mean_sea_level=on&lev_surface=on&var_PRES=on&var_PRMSL=on&leftlon=0&rightlon=360&toplat=90&bottomlat=-90&dir=%2Fnam.20200811
 
                
                
                elif (model_name == 'gfs'):       
                    # gfs 
                    # works
                    # curl_command = 'curl "https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl?file=gfs.t12z.pgrb2.0p25.f000&lev_mean_sea_level=on&lev_surface=on&var_PRES=on&var_PRMSL=on&subregion=&leftlon=-160&rightlon=-110&toplat=50&bottomlat=25&dir=%2Fgfs.20200810%2F12" -o '+file_name_ingest
                    # curl_command = 'curl "https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl?file=gfs.t12z.pgrb2.0p25.f000&lev_mean_sea_level=on&lev_surface=on&var_PRES=on&var_PRMSL=on&subregion=&leftlon=-160&rightlon=-110&toplat=50&bottomlat=25&dir=%2F'+url_folder_str1+'%2F12" -o '+file_name_ingest
                    # use this one 

curl_command = 'curl "https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl?file=gfs.t'+dt_init.strftime('%H')+'z.pgrb2.0p25.f'+str(hr).zfill(3)+'&lev_mean_sea_level=on&lev_surface=on&var_PRES=on&var_PRMSL=on&subregion=&leftlon=-160&rightlon=-110&toplat=50&bottomlat=25&dir=%2F'+url_folder_str1+'%2F12" -o '+file_name_ingest


                 
                print      ('    curl_command is %s ' % (curl_command))
                logger.info('    curl_command is %s ' % (curl_command))
                process_check = subprocess.Popen(curl_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                out,err = process_check.communicate(timeout=3*60) # 2 min doesnt seem to be long enough    
                #if ('404 Not Found' in out_str):  # file does not exist 
                #elif   ('200 OK' in out_str): # file exists 
                if   (process_check.returncode == 0):  
                    print      ('    download_forecast_grid_and_write_to_local: file successfully downloaded ')
                    logger.info('    download_forecast_grid_and_write_to_local: file successfully downloaded ')
                    #update_forecasts_available_table(logger, cursor, connection, autocommit, table_name, datetime_init_temp, forecast_horizon_hr)
                elif (process_check.returncode != 0): # file does not exist 
                    print      ('    ERROR download_forecast_grid_and_write_to_local: file not downloaded successfully ')
                    logger.info('    ERROR download_forecast_grid_and_write_to_local: file not downloaded successfully ')
                    print      ('    download_forecast_grid_and_write_to_local: process_check.returncode is %s' %(process_check.returncode)) 
                    logger.info('    download_forecast_grid_and_write_to_local: process_check.returncode is %s' %(process_check.returncode)) 
                    print      ('    download_forecast_grid_and_write_to_local: out is %s' %(out)) 
                    logger.info('    download_forecast_grid_and_write_to_local: out is %s' %(out)) 
                    print      ('    download_forecast_grid_and_write_to_local: err is %s' %(err)) 
                    logger.info('    download_forecast_grid_and_write_to_local: err is %s' %(err)) 
                 
        if   (model_name == 'gfs' and hr > 120):        
            hr += 3
        if   (model_name == 'nam' and hr > 36):        
            hr += 3
        else:
            hr += 1

            
###############################################################################
def process_data(model_name, dt_init, forecast_horizon_hr, bucket_name):

    
    # read station data 
    use_stn = 'all'
    print_stn_info = 1
    #read_stn_metadata_type = 'csv' # 'db' or 'csv'
    project_name = 'pgrad'
    stn_metadata_file_name = os.path.join(os.environ['HOME'], project_name, 'station_list_'+project_name+'.csv') 
    (dict_stn_metadata) = read_stn_metadata_from_csv(stn_metadata_file_name, use_stn, print_stn_info)


    dir_init_temp = dt_init.strftime('%Y-%m-%d')
    dir_name_ingest    = os.path.join('data', 'ingest',    dir_init_temp)
    dir_name_processed = os.path.join('data', 'processed', dir_init_temp)
    
    # get list of files in ingest dir
    file_list = glob.glob(os.path.join(dir_name_ingest, '*'))
    n_files = len(file_list)
    print      ('found %s files to process' %(n_files))
    logger.info('found %s files to process' %(n_files))

    file_temp = file_list[0]
    for file_temp in file_list: 
        #file_name = os.path.dirname(file_temp)
        file_name = os.path.basename(file_temp)
        file_name_processed = os.path.join(dir_name_processed, file_name)


#cfgrib.open_datasets(file_temp)


ds_read = xr.open_dataset(file_temp, engine='cfgrib')

'heightAboveGround',
 'latitude',
 'longitude',
 'meanSea',
 'prmsl',
 'sp',
 'step',
 'surface',
 'time',
 'valid_time'

sorted(ds_read.variables)



# hrrr, and nam
lon_2d = np.array(ds_read['longitude'])
lat_2d = np.array(ds_read['latitude'])
p_sfc_2d = np.array(ds_read['sp'])
dt_read = ds_sfc['time']
ds_read['time']
ds_read['valid_time']
ds_read['meanSea']
# mmean sea level pressur
# hrrr
ds_read['mslma']
# nam
ds_read['prmsl']






ds_sfc = xr.open_dataset(file_temp, engine='cfgrib',
     backend_kwargs={'filter_by_keys': {'typeOfLevel': 'surface'}})
ds_2m = xr.open_dataset(file_temp, engine='cfgrib',
      backend_kwargs={'filter_by_keys': {'typeOfLevel': 'heightAboveGround', 'level': 2}})
ds_10m = xr.open_dataset(file_temp, engine='cfgrib',
     backend_kwargs={'filter_by_keys': {'typeOfLevel': 'heightAboveGround', 'level': 10}})

ds_sfc
ds_2m
ds_10m

hrrr
sfc
lat, lon, time, valid_time, sp, orog
mslma





ds_sfc = xr.open_dataset(file_temp, engine='cfgrib',
     backend_kwargs={'filter_by_keys': {'typeOfLevel': 'surface'}})
ds_2m = xr.open_dataset(file_temp, engine='cfgrib',
      backend_kwargs={'filter_by_keys': {'typeOfLevel': 'heightAboveGround', 'level': 2}})
ds_10m = xr.open_dataset(file_temp, engine='cfgrib',
     backend_kwargs={'filter_by_keys': {'typeOfLevel': 'heightAboveGround', 'level': 10}})

ds_sfc
ds_2m
ds_10m

hrrr
sfc
lat, lon, time, valid_time, sp, orog
mslma

ds_read = xr.open_dataset(file_temp, engine='cfgrib')

lon_2d = np.array(ds_read['longitude'])
lat_2d = np.array(ds_read['latitude'])
sfs_pres_2d = np.array(ds_read['sp'])

dt_read = ds_sfc['time']


sorted(ds_read.variables)

ds_read['time']
ds_read['valid_time']
# mmean sea level pressur
ds_read['mslma']


ds_read['meanSea']


,
     backend_kwargs={'filter_by_keys': {'typeOfLevel': 'surface'}})



ds_sfc.close()
ds_2m.close()
ds_10m.close()
del ds_sfc
del ds_2m
del ds_10m


ds_sfc.variables

sfc
sp - surface pressure

file_name_temp_ingest = os.path.join(dir_work, 'nam_static.grib2')

hgt_2d = np.array(ds_sfc['orog'])
hgt_2d = hgt_2d*3.28084 # m to ft

if not (initial_read):
    lon_2d = numpy.array(ds_10m['longitude'])
    lat_2d = numpy.array(ds_10m['latitude'])
    hgt_2d = numpy.array(ds_sfc['orog'])
    hgt_2d = hgt_2d*3.28084 # m to ft
    [ny, nx] = numpy.shape(lon_2d)
    ws10_2d_hr  = numpy.full([ny, nx, n_hrs], numpy.nan, dtype=float)
    wsg10_2d_hr = numpy.full([ny, nx, n_hrs], numpy.nan, dtype=float)
    initial_read = True    
u_ws10_2d = numpy.array(ds_10m['u10'])
v_ws10_2d = numpy.array(ds_10m['v10'])
wsg10_2d = numpy.array(ds_sfc['gust'])
ws10_2d = numpy.sqrt(u_ws10_2d**2.0 + v_ws10_2d**2.0)
ws10_2d_hr [:,:,hr] = ws10_2d 
wsg10_2d_hr[:,:,hr] = wsg10_2d 
del u_ws10_2d, v_ws10_2d, wsg10_2d, ws10_2d

lon_2d = lon_2d - 360.0        



    dt_valid_temp = dt_min_plot_utc + td(hours=hr)
    print      ('  reading %s UTC ' %(dt_valid_temp.strftime('%Y-%m-%d_%H')))
    logger.info('  reading %s UTC ' %(dt_valid_temp.strftime('%Y-%m-%d_%H')))
    (file_name_temp_ingest, file_name_temp_archive) = build_model_local_file_names(logger, model_name, dt_init_utc, dt_valid_temp, dir_data_model_raw_ingest, dir_data_model_raw_archive)
    if not (os.path.isfile(file_name_temp_ingest)) or (os.path.isfile(file_name_temp_archive)):
        print      ('  ERROR missing file ')
        logger.info('  ERROR missing file ')
        #sys.exit()
    else: # file exists
        # ds = xarray.open_dataset(file_name_temp_ingest, engine='cfgrib')




# process data - 4 hr 
# 4    read grib file w/ xarray
# 5    grab pres/slp values at stn locations 
# 7    read/create/write pres_csv 
# 8    move files from ingest to archive
# 9a   works for gfs, nam, and hrrr






        print      ('    processing hr %s of %s ' % (hr, forecast_horizon_hr))
        logger.info('    processing hr %s of %s ' % (hr, forecast_horizon_hr))    
        dir_init_temp = dt_init.strftime('%Y-%m-%d')
        file_name = model_name+'_'+dt_init.strftime('%Y-%m-%d_%H')+'_t_'+str(hr).rjust(2,'0')+'.grib2'
        dir_name_ingest    = os.path.join('data', 'ingest',    dir_init_temp)
        dir_name_processed = os.path.join('data', 'processed', dir_init_temp)
        file_name_ingest    = os.path.join(dir_name_ingest, file_name)
        file_name_processed = os.path.join(dir_name_processed, file_name)
        print      ('    file_ingest %s, file_processed %s ' % (file_name_ingest, file_name_processed))
        logger.info('    file_ingest %s, file_processed %s ' % (file_name_ingest, file_name_processed))
        # mkdir if doesnt exist
        if not os.path.isdir(dir_name_ingest):
            os.system('mkdir -p '+dir_name_ingest)
        if not os.path.isdir(dir_name_processed):
            os.system('mkdir -p '+dir_name_processed)
        #if   (model_name == 'hrrr'):        
        #elif (model_name == 'nam'):        

        if not (os.path.isfile(file_name_ingest) or os.path.isfile(file_name_processed)):
            # check if exists on remote            
            if   (model_name == 'hrrr'):
                base_url = 'https://nomads.ncep.noaa.gov/pub/data/nccf/com/hrrr/prod/hrrr.'
                url_folder_str = dt_init.strftime('%Y')+dt_init.strftime('%m')+dt_init.strftime('%d')
                file_name_remote = model_name+'.t'+dt_init.strftime('%H')+'z.wrfsfcf'+str(hr).rjust(2,'0')+'.grib2'
                url_temp = base_url+url_folder_str+'/conus/'+file_name_remote
            elif (model_name == 'nam'):
                base_url = 'https://nomads.ncep.noaa.gov/pub/data/nccf/com/nam/prod/nam.'
                url_folder_str = dt_init.strftime('%Y')+dt_init.strftime('%m')+dt_init.strftime('%d')
                file_name_remote = model_name+'.t'+dt_init.strftime('%H')+'z.conusnest.hiresf'+str(hr).rjust(2,'0')+'.tm00.grib2'
                url_temp = base_url+url_folder_str+'/'+file_name_remote
            elif (model_name == 'gfs'):
                base_url = 'https://nomads.ncep.noaa.gov/pub/data/nccf/com/'+model_name+'/prod/'
                url_folder_str1 = model_name+'.'+dt_init.strftime('%Y%m%d')
                url_folder_str2 = dt_init.strftime('%H')                
                file_name_remote = model_name+'.t'+dt_init.strftime('%H')+'z.pgrb2.0p25.f'+str(hr).zfill(3)
                url_temp = base_url+url_folder_str1+'/'+url_folder_str2+'/'+file_name_remote
            print      ('    url_temp is %s ' % (url_temp))
            logger.info('    url_temp is %s ' % (url_temp))
  
            #response = requests.head(url_temp+'no')
            response = requests.head(url_temp)
            #response.headers
            if response.status_code != 200: # 404 not found
                file_exists_on_remote = False
                print      ('    file does not exist on remote')
                logger.info('    file does not exist on remote')
                break
            else:             
                print      ('    file exists on remote')
                logger.info('    file exists on remote')
  
                if   (model_name == 'hrrr'):
                    # works 
                    curl_command = 'curl "https://nomads.ncep.noaa.gov/cgi-bin/filter_hrrr_2d.pl?file='+file_name_remote+'&lev_10_m_above_ground=on&lev_2_m_above_ground=on&lev_surface=on&var_HGT=on&var_PRES=on&var_RH=on&var_TMP=on&var_UGRD=on&var_VGRD=on&var_APCP=on&var_DPT=on&var_FRICV=on&var_GUST=on&var_LAND=on&var_WIND=on&var_HGT=on&var_PRES=on&var_RH=on&var_TMP=on&var_UGRD=on&var_VGRD=on&subregion=&leftlon=-160&rightlon=-110&toplat=50&bottomlat=25&dir=%2Fhrrr.'+url_folder_str+'%2Fconus" -o '+file_name_ingest
                
                elif (model_name == 'nam'):
                    # nam   
                    # curl_command = 'curl "https://nomads.ncep.noaa.gov/cgi-bin/filter_nam.pl?file=nam.t00z.awphys00.tm00.grib2&lev_10_m_above_ground=on&lev_mean_sea_level=on&lev_surface=on&var_PRES=on&var_PRMSL=on&var_UGRD=on&var_VGRD=on&subregion=&leftlon=-160&rightlon=-110&toplat=50&bottomlat=25&dir=%2Fnam.20200810" -o '+file_name_ingest
                    # curl_command = 'curl "https://nomads.ncep.noaa.gov/cgi-bin/filter_nam.pl?file=nam.t00z.awphys00.tm00.grib2&lev_10_m_above_ground=on&lev_mean_sea_level=on&lev_surface=on&var_PRES=on&var_PRMSL=on&var_UGRD=on&var_VGRD=on&subregion=&leftlon=-160&rightlon=-110&toplat=50&bottomlat=25&dir=%2Fnam.'+url_folder_str+'" -o '+file_name_ingest
                    # use this one
                    curl_command = 'curl "https://nomads.ncep.noaa.gov/cgi-bin/filter_nam.pl?file=nam.t'+dt_init.strftime('%H')+'z.awphys'+str(hr).zfill(2)+'.tm00.grib2&lev_10_m_above_ground=on&lev_mean_sea_level=on&lev_surface=on&var_PRES=on&var_PRMSL=on&var_UGRD=on&var_VGRD=on&subregion=&leftlon=-160&rightlon=-110&toplat=50&bottomlat=25&dir=%2Fnam.'+url_folder_str+'" -o '+file_name_ingest
                
                elif (model_name == 'gfs'):       
                    # gfs 
                    # works
                    # curl_command = 'curl "https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl?file=gfs.t12z.pgrb2.0p25.f000&lev_mean_sea_level=on&lev_surface=on&var_PRES=on&var_PRMSL=on&subregion=&leftlon=-160&rightlon=-110&toplat=50&bottomlat=25&dir=%2Fgfs.20200810%2F12" -o '+file_name_ingest
                    # curl_command = 'curl "https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl?file=gfs.t12z.pgrb2.0p25.f000&lev_mean_sea_level=on&lev_surface=on&var_PRES=on&var_PRMSL=on&subregion=&leftlon=-160&rightlon=-110&toplat=50&bottomlat=25&dir=%2F'+url_folder_str1+'%2F12" -o '+file_name_ingest
                    # use this one 
                    curl_command = 'curl "https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl?file=gfs.t'+dt_init.strftime('%H')+'z.pgrb2.0p25.f'+str(hr).zfill(3)+'&lev_mean_sea_level=on&lev_surface=on&var_PRES=on&var_PRMSL=on&subregion=&leftlon=-160&rightlon=-110&toplat=50&bottomlat=25&dir=%2F'+url_folder_str1+'%2F12" -o '+file_name_ingest
                    
                
                print      ('    curl_command is %s ' % (curl_command))
                logger.info('    curl_command is %s ' % (curl_command))
                process_check = subprocess.Popen(curl_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                out,err = process_check.communicate(timeout=3*60) # 2 min doesnt seem to be long enough    
                #if ('404 Not Found' in out_str):  # file does not exist 
                #elif   ('200 OK' in out_str): # file exists 
                if   (process_check.returncode == 0):  
                    print      ('    download_forecast_grid_and_write_to_local: file successfully downloaded ')
                    logger.info('    download_forecast_grid_and_write_to_local: file successfully downloaded ')
                    #update_forecasts_available_table(logger, cursor, connection, autocommit, table_name, datetime_init_temp, forecast_horizon_hr)
                elif (process_check.returncode != 0): # file does not exist 
                    print      ('    ERROR download_forecast_grid_and_write_to_local: file not downloaded successfully ')
                    logger.info('    ERROR download_forecast_grid_and_write_to_local: file not downloaded successfully ')
                    print      ('    download_forecast_grid_and_write_to_local: process_check.returncode is %s' %(process_check.returncode)) 
                    logger.info('    download_forecast_grid_and_write_to_local: process_check.returncode is %s' %(process_check.returncode)) 
                    print      ('    download_forecast_grid_and_write_to_local: out is %s' %(out)) 
                    logger.info('    download_forecast_grid_and_write_to_local: out is %s' %(out)) 
                    print      ('    download_forecast_grid_and_write_to_local: err is %s' %(err)) 
                    logger.info('    download_forecast_grid_and_write_to_local: err is %s' %(err)) 
                 
        if   (model_name == 'gfs' and hr > 120):        
            hr += 3
        if   (model_name == 'nam' and hr > 36):        
            hr += 3
        else:
            hr += 1



###############################################################################    
if __name__ == "__main__":
    #n_files  = int(sys.argv[1])
    #print('processing %s files' %(n_files))
    #analyze_batteries(n_files)

    #python ./src/battery_analysis.py 5
    #python ./src/pgrad.py model_name=hrrr process_type=operational bucket_name=pgrad
    #python ./src/pgrad.py model_name=gfs process_type=backfill bucket_name=pgrad

    os.chdir('/home/csmith/pgrad')
    model_name = 'hrrr'    
    #model_name = 'nam'    
    #model_name = 'gfs'    
    batching_mode = 'operational'
    #batching_mode = 'backfill'
    process_name = 'download'
    #process_name = 'process'
    #process_name = 'plot'
    bucket_name = 'data'
    
    # parse inputs 
    parser = argparse.ArgumentParser(description='argparse')
    parser.add_argument('--model_name',    type=str, help='gfs/nam/hrrr', required=True, default='gfs')
    parser.add_argument('--process_name',  type=str, help='download/process/plot', required=True, default='download')    
    parser.add_argument('--batching_mode', type=str, help='operational/backfill', required=True, default='operational')    
    parser.add_argument('--bucket_name',   type=str, help='bucket_name', required=True, default='pgrad')
    args = parser.parse_args()
    model_name    = args.model_name
    process_name  = args.process_name 
    batching_mode = args.batching_mode 
    bucket_name   = args.bucket_name
 
    # sanitize inputs
    if model_name not in ['gfs', 'nam', 'hrrr']:
        print('ERROR model_name %s not supported' %(model_name))
        sys.exit()
    if process_name not in ['download','process','plot']:
        print('ERROR model_name %s not supported' %(process_name))
        sys.exit()
    if batching_mode not in ['operational','backfill']:
        print('ERROR batching_mode %s not supported' %(batching_mode))
        sys.exit()

    if   model_name == 'gfs':
        forecast_horizon_hr = 24*10
    elif model_name == 'nam':
        forecast_horizon_hr = 24*5
    elif model_name == 'hrrr':
        forecast_horizon_hr = 36
        
    update_frequency_hrs = 6
    # define starting time 
    print      ('define_cron_start_time and local daylight savings time ') 
    dt_start_utc = dt.utcnow()    
    (utc_conversion, time_zone_label) = define_daylight_savings_or_not(dt_start_utc) 
    dt_start_lt = dt.utcnow() - td(hours=utc_conversion)
    
    # create_log_file
    print      ('create_log_file' ) 
    log_file_name = 'log_'+process_name+'_'+dt_start_lt.strftime('%Y-%m-%d_%H-%M')+'.txt' 
    log_name_full_file_path = os.path.join('logs', log_file_name) 
    logger = create_log_file(log_name_full_file_path, dt_start_utc, time_zone_label) 

    # get next expected forecast to be available 
    dt_init_expected = define_expected_forecast_available_from_wallclock(logger, model_name, update_frequency_hrs)
    
    if   batching_mode == 'operational':
        hours_to_backfill = 0
    elif batching_mode == 'backfill':
        hours_to_backfill = 24

    dt_init = dt_init_expected
    while dt_init >= dt_init_expected - td(hours=hours_to_backfill): 
        print      ('  processing init %s ' % (dt_init.strftime('%Y-%m-%d_%H-%M')))
        logger.info('  processing init %s ' % (dt_init.strftime('%Y-%m-%d_%H-%M')))
        print('executing process %s' %(process_name))
        if   process_name == 'download':
            download_data(model_name, dt_init, forecast_horizon_hr, bucket_name)
        elif process_name == 'process':
            process_data(model_name, dt_init, forecast_horizon_hr, bucket_name)
        if   process_name == 'plot':
            plot_data(model_name, dt_init, forecast_horizon_hr, bucket_name)
        dt_init = dt_init - td(hours=update_frequency_hrs)
        
    # close log file
    print      ('close_logger begin ')
    logger.info('close_logger begin ')
    close_logger(logger, process_name, dt_start_lt, utc_conversion, time_zone_label) 

###############################################################################    




