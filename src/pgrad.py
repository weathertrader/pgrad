    
'''
name: pgrad.py 
purpose: process and analyze pressure gradient forcing from NWP models 
author: Craig Smith, craig.matthew.smith@gmail.com
usage: ./src/run.sh n  where n is the number of batteries to analyze [1-5]
repo: https://github.com/weathertrader/battery_charge
'''

import os
import sys
import csv
import argparse 
import pandas as pd
import numpy as np
import xarray as xr
# import cfgrib
#from netCDF4 import Dataset 
import time
from datetime import datetime as dt 
from datetime import timedelta as td 
import glob
import requests
import pymongo
from pymongo import MongoClient
import subprocess
import matplotlib
# plotting from cli
matplotlib.use('Agg') 
#matplotlib.use('Agg',warn=False) 
import matplotlib.pyplot as plt
from matplotlib.dates import drange, DateFormatter
from matplotlib.ticker import MultipleLocator 
import warnings
import math
import logging 

###############################################################################    
def create_log_file(log_name_full_file_path, dt_start_utc, time_zone_label):
    
    use_new_logger = False
    if not use_new_logger: 
        if not (os.path.isdir(os.path.dirname(log_name_full_file_path))):
            #os.mkdir(os.path.dirname(log_name_full_file_path))
            os.system('mkdir -p '+os.path.dirname(log_name_full_file_path))    
        formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(module)s - %(message)s') 
        logger    = logging.getLogger(log_name_full_file_path)
        handler   = logging.FileHandler(log_name_full_file_path) 
        handler.setFormatter(formatter) 
        logger.addHandler(handler) 
        logger.setLevel(logging.INFO) # INFO, DEBUG,INFO,WARNING,ERROR,CRITICAL    
    else: # new_logger 
        #logging.basicConfig(level=logging.DEBUG, filename='app2.log', format='%(name)s %(asctime)s %(levelname)s:%(message)s')
        logging.basicConfig(level=logging.DEBUG, format='%(name)s %(asctime)s %(levelname)s:%(message)s')
        logger = logging.getLogger(__name__)
        try:
          c = 4 / 0
        except Exception as e:
          logger.error("Exception occurred", exc_info=True)
        logger.info("logger info")
        logger.warning("logger warning")
        logger.debug("logger debug")
        logger.error("logger error")
    
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
    time_delta_minutes = (dt_end_lt - dt_start_lt).seconds/60.0
    print      ('###############################################################################') 
    logger.info('###############################################################################') 
    print      ('total_time %s %6.2f minutes, %s - %s [%s]  ' % (process_name, time_delta_minutes, dt_start_lt.strftime('%Y-%m-%d_%H-%M'), dt_end_lt.strftime('%Y-%m-%d_%H-%M'), time_zone_label))
    logger.info('total_time %s %6.2f minutes, %s - %s [%s]  ' % (process_name, time_delta_minutes, dt_start_lt.strftime('%Y-%m-%d_%H-%M'), dt_end_lt.strftime('%Y-%m-%d_%H-%M'), time_zone_label))    
    
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

    #dt_init_expected -= td(hours=6)

    print      ('  expecting %s %s Z to be available ' % (model_name, dt_init_expected.strftime('%Y-%m-%d %H')))
    logger.info('  expecting %s %s Z to be available ' % (model_name, dt_init_expected.strftime('%Y-%m-%d %H')))

    return dt_init_expected


###############################################################################
def read_stn_metadata_from_csv(stn_metadata_file_name, use_stn, print_stn_info):
    '''read station metadata'''
 
    stn_read_df = pd.read_csv(stn_metadata_file_name,index_col=0)
    stn_name = stn_read_df['stn_name'].values
    stn_id   = stn_read_df['stn_id'].values
    stn_lon  = stn_read_df['stn_lon'].values
    stn_lat  = stn_read_df['stn_lat'].values
    stn_ele  = stn_read_df['stn_ele'].values
    stn_obs_hgt = stn_read_df['stn_obs_hgt'].values
    stn_mnet_id = stn_read_df['stn_mnet_id'].values
    stn_tmzn = stn_read_df['stn_tmzn'].values
    stn_dt_start = stn_read_df['stn_datetime_start'].values
    stn_dt_end = stn_read_df['stn_datetime_end'].values
    stn_state = stn_read_df['stn_state'].values
    stn_county = stn_read_df['stn_county'].values
    n_stn = len(stn_lat)
    
    del stn_read_df
    
    print ('use_stn is %s ' % (use_stn)) 
 
    if (use_stn != 'all'): 
        if   ('mnet' in use_stn):  
            use_stn_split = use_stn.split('=')
            mnet_id_list = use_stn_split[-1]
            mnet_id_list = mnet_id_list.split(',')
            n_mnet_id = len(mnet_id_list)            
            mnet_id_int = []
            for nm in range(0,n_mnet_id,1): 
                mnet_id_int.append(int(mnet_id_list[nm]))     
            use_stn = []
            for s in range(0,n_stn,1):
               # if (stn_mnet_id[s] == mnt_id_int): 
               if (stn_mnet_id[s] in mnet_id_int): 
                   use_stn.append(s)
        elif ('mnet' not in use_stn):  
            use_stn_split = use_stn.split(',')
            n_stn = len(use_stn_split)
            use_stn = []
            for s in range(0, n_stn, 1):
                use_stn.append(int(use_stn_split[s]))  
        
        stn_name           = stn_name          [use_stn]
        stn_id             = stn_id            [use_stn] 
        stn_lon            = stn_lon           [use_stn] 
        stn_lat            = stn_lat           [use_stn] 
        stn_ele            = stn_ele           [use_stn] 
        stn_obs_hgt        = stn_obs_hgt       [use_stn]   
        stn_mnet_id        = stn_mnet_id       [use_stn]
        stn_tmzn           = stn_tmzn          [use_stn]
        stn_datetime_start = stn_datetime_start[use_stn] 
        stn_datetime_end   = stn_datetime_end  [use_stn] 
        #stn_state          = stn_state         [use_stn] 
        #stn_county         = stn_county        [use_stn] 
        #stn_cwa            = stn_cwa           [use_stn] 
        #stn_notes          = stn_notes         [use_stn] 

    n_stn = len(stn_lat)
    if (print_stn_info): 
        print ('station infomation list ') 
        # for s,stn_name_temp in enumerate(stn_name):          
        for s in range(0, n_stn, 1): 
           #print ('  stn_id %s lon %s lat %s ele %s obs_hgt %s ' % (stn_id[s], stn_lon[s], stn_lat[s], stn_ele[s], stn_obs_hgt[s])) 
           print ('  %s, lon %2.2f, lat %2.2f, ele %6.2f obs_hgt %2.1f, %s ' % (stn_id[s], stn_lon[s], stn_lat[s], stn_ele[s], stn_obs_hgt[s], stn_name[s])) 

    stn_metadata_dict = {}
    stn_metadata_dict['stn_name']           = stn_name
    stn_metadata_dict['stn_id']             = stn_id
    stn_metadata_dict['stn_lon']            = stn_lon
    stn_metadata_dict['stn_lat']            = stn_lat
    stn_metadata_dict['stn_ele']            = stn_ele
    stn_metadata_dict['stn_obs_hgt']        = stn_obs_hgt
    stn_metadata_dict['stn_mnet_id']        = stn_mnet_id
    stn_metadata_dict['stn_tmzn']           = stn_tmzn
    stn_metadata_dict['stn_dt_start']       = stn_dt_start
    stn_metadata_dict['stn_dt_end']         = stn_dt_end
    #stn_metadata_dict['stn_state']          = stn_state
    #stn_metadata_dict['stn_county']         = stn_county
    #stn_metadata_dict['stn_cwa']            = stn_cwa
    stn_metadata_dict['n_stn']              = n_stn 

    return stn_metadata_dict 


###############################################################################
def map_stn_locations_to_grid_locations(logger, stn_metadata_dict, lon_2d, lat_2d, print_flag):
    ''' find grid indices of station locations'''
    i_loc_s = np.zeros([stn_metadata_dict['n_stn']], dtype='int') 
    j_loc_s = np.zeros([stn_metadata_dict['n_stn']], dtype='int') 
    s = 0
    for s in range(0, stn_metadata_dict['n_stn'], 1):
        total_diff_2d = np.abs(lon_2d - stn_metadata_dict['stn_lon'][s]) + np.abs(lat_2d - stn_metadata_dict['stn_lat'][s])
        #[j_loc_s[s], i_loc_s[s]] = np.unravel_index(total_diff_2d.argmin(), total_diff_2d.shape)
        [j_loc_s[s], i_loc_s[s]] = np.argwhere(total_diff_2d == np.min(total_diff_2d))[0]
        del total_diff_2d                
    if (print_flag):
        s = 0
        for s in range(0, stn_metadata_dict['n_stn'], 1): 
            print ('processing s %s of %s ' % (s, stn_metadata_dict['n_stn']))
            print ('  lon expected %2.2f found %2.2f ' % (stn_metadata_dict['stn_lon'][s], lon_2d[j_loc_s[s],i_loc_s[s]]))
            print ('  lat expected %2.2f found %2.2f ' % (stn_metadata_dict['stn_lat'][s], lat_2d[j_loc_s[s],i_loc_s[s]]))            
    return j_loc_s, i_loc_s 


###############################################################################
def download_data(model_name, dt_init, forecast_horizon_hr, bucket_name):

    print      ('download_data begin ')
    logger.info('download_data begin ')
    
    hr = 0
    file_exists_on_remote = True
    while hr < forecast_horizon_hr and file_exists_on_remote:
        print      ('  processing hr %s of %s ' % (hr, forecast_horizon_hr))
        logger.info('  processing hr %s of %s ' % (hr, forecast_horizon_hr))    
        dir_init_temp = dt_init.strftime('%Y-%m-%d')
        file_name = model_name+'_'+dt_init.strftime('%Y-%m-%d_%H')+'_t_'+str(hr).rjust(2,'0')+'.grib2'
        dir_name_ingest    = os.path.join('data', 'ingest',    dir_init_temp)
        dir_name_processed = os.path.join('data', 'processed', dir_init_temp)
        file_name_ingest    = os.path.join(dir_name_ingest, file_name)
        file_name_processed = os.path.join(dir_name_processed, file_name)
        print_file_names = False
        if print_file_names:
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
                # old gfs                
                # https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.20210327/12/      gfs.t12z.pgrb2.0p25.f000                
                # new gfs 2021/03 
                # https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.20210327/12/atmos/gfs.t12z.pgrb2.0p25.f000                
                base_url = 'https://nomads.ncep.noaa.gov/pub/data/nccf/com/'+model_name+'/prod/'
                url_folder_str1 = model_name+'.'+dt_init.strftime('%Y%m%d')
                url_folder_str2 = dt_init.strftime('%H')                
                file_name_remote = model_name+'.t'+dt_init.strftime('%H')+'z.pgrb2.0p25.f'+str(hr).zfill(3)
                #url_temp = base_url+url_folder_str1+'/'+url_folder_str2+'/'+file_name_remote
                url_temp = base_url+url_folder_str1+'/'+url_folder_str2+'/atmos/'+file_name_remote
            print_grib_url = False
            if print_grib_url:
                print      ('    url_temp is %s ' % (url_temp))
                logger.info('    url_temp is %s ' % (url_temp))
  
            #response = requests.head(url_temp+'no')
            response = requests.head(url_temp)
            #response.headers
            if response.status_code != 200: # 404 not found
                file_exists_on_remote = False
                print      ('    file does not exist on remote')
                logger.info('    file does not exist on remote')
                return
            else:             
                print      ('    file exists on remote')
                logger.info('    file exists on remote')
  
                if   (model_name == 'hrrr'):
                    # curl_command = 'curl "https://nomads.ncep.noaa.gov/cgi-bin/filter_hrrr_2d.pl?file='+file_name_remote+'&lev_10_m_above_ground=on&lev_2_m_above_ground=on&lev_surface=on&var_HGT=on&var_PRES=on&var_RH=on&var_TMP=on&var_UGRD=on&var_VGRD=on&var_APCP=on&var_DPT=on&var_FRICV=on&var_GUST=on&var_LAND=on&var_WIND=on&var_HGT=on&var_PRES=on&var_RH=on&var_TMP=on&var_UGRD=on&var_VGRD=on&subregion=&leftlon=-160&rightlon=-110&toplat=50&bottomlat=25&dir=%2Fhrrr.'+url_folder_str+'%2Fconus" -o '+file_name_ingest
                    # curl_command = 'curl "https://nomads.ncep.noaa.gov/cgi-bin/filter_hrrr_2d.pl?file='+file_name_remote+'&lev_2_m_above_ground=on&lev_mean_sea_level=on&lev_surface=on&var_HGT=on&var_MSLMA=on&var_PRES=on&var_APCP=on&var_UGRD=on&var_VGRD=on&subregion=&leftlon=-160&rightlon=-110&toplat=50&bottomlat=25&dir=%2Fhrrr.'+url_folder_str+'%2Fconus" -o '+file_name_ingest
                    # curl_command = 'curl "https://nomads.ncep.noaa.gov/cgi-bin/filter_hrrr_2d.pl?file='+file_name_remote+'&lev_mean_sea_level=on&lev_surface=on&var_HGT=on&var_MSLMA=on&var_PRES=on&var_UGRD=on&var_VGRD=on&subregion=&leftlon=-160&rightlon=-110&toplat=50&bottomlat=25&dir=%2Fhrrr.'+url_folder_str+'%2Fconus" -o '+file_name_ingest
                    # curl_command = 'curl "https://nomads.ncep.noaa.gov/cgi-bin/filter_hrrr_2d.pl?file='+file_name_remote+'&lev_mean_sea_level=on&lev_surface=on&var_HGT=on&var_MSLMA=on&var_PRES=on&subregion=&leftlon=-160&rightlon=-110&toplat=50&bottomlat=25&dir=%2Fhrrr.'+url_folder_str+'%2Fconus" -o '+file_name_ingest
                    curl_command = 'curl "https://nomads.ncep.noaa.gov/cgi-bin/filter_hrrr_2d.pl?file='+file_name_remote+'&lev_mean_sea_level=on&lev_surface=on&var_HGT=on&var_MSLMA=on&var_PRES=on&subregion=&leftlon=-160&rightlon=-110&toplat=50&bottomlat=25&dir=%2Fhrrr.'+url_folder_str+'%2Fconus" -o '+file_name_ingest
                
                
                elif (model_name == 'nam'):
                    # previous
                    # curl_command = 'curl "https://nomads.ncep.noaa.gov/cgi-bin/filter_nam.pl?file=nam.t'+dt_init.strftime('%H')+'z.awphys'+str(hr).zfill(2)+'.tm00.grib2&lev_mean_sea_level=on&lev_surface=on&var_PRES=on&var_PRMSL=on&subregion=&leftlon=-160&rightlon=-110&toplat=50&bottomlat=25&dir=%2Fnam.'+url_folder_str+'" -o '+file_name_ingest
                    # new?    
                    curl_command = 'curl "https://nomads.ncep.noaa.gov/cgi-bin/filter_nam_conusnest.pl?file=nam.t'+dt_init.strftime('%H')+'z.conusnest.hiresf'+str(hr).zfill(2)+'.tm00.grib2&lev_mean_sea_level=on&lev_surface=on&var_PRES=on&var_PRMSL=on&subregion=&leftlon=-160&rightlon=-110&toplat=50&bottomlat=25&dir=%2Fnam.'+url_folder_str+'" -o '+file_name_ingest
                    #                     https://nomads.ncep.noaa.gov/cgi-bin/filter_nam_conusnest.pl?file=nam.t00                        z.conusnest.hiresf00                  .tm00.grib2&lev_mean_sea_level=on&lev_surface=on&var_PRES=on&var_PRMSL=on&subregion=&leftlon=-160&rightlon=-110&toplat=50&bottomlat=25&dir=%2Fnam.20200919
                    
                    # nam   
                    # curl_command = 'curl "https://nomads.ncep.noaa.gov/cgi-bin/filter_nam.pl?file=nam.t00z.awphys00.tm00.grib2&lev_10_m_above_ground=on&lev_mean_sea_level=on&lev_surface=on&var_PRES=on&var_PRMSL=on&var_UGRD=on&var_VGRD=on&subregion=&leftlon=-160&rightlon=-110&toplat=50&bottomlat=25&dir=%2Fnam.20200810" -o '+file_name_ingest
                    # curl_command = 'curl "https://nomads.ncep.noaa.gov/cgi-bin/filter_nam.pl?file=nam.t00z.awphys00.tm00.grib2&lev_10_m_above_ground=on&lev_mean_sea_level=on&lev_surface=on&var_PRES=on&var_PRMSL=on&var_UGRD=on&var_VGRD=on&subregion=&leftlon=-160&rightlon=-110&toplat=50&bottomlat=25&dir=%2Fnam.'+url_folder_str+'" -o '+file_name_ingest
                    # use this one
                    # nam conus
                    # https://nomads.ncep.noaa.gov/cgi-bin/filter_nam.pl?file=nam.t00z.awphys00.tm00.grib2&lev_mean_sea_level=on&lev_surface=on&var_PRES=on&var_PRMSL=on&leftlon=0&rightlon=360&toplat=90&bottomlat=-90&dir=%2Fnam.20200811
                    # nam hires nest 
                    # https://nomads.ncep.noaa.gov/cgi-bin/filter_nam_conusnest.pl?file=nam.t00z.conusnest.hiresf00.tm00.grib2&lev_mean_sea_level=on&lev_surface=on&var_PRES=on&var_PRMSL=on&leftlon=0&rightlon=360&toplat=90&bottomlat=-90&dir=%2Fnam.20200811
  
                elif (model_name == 'gfs'):       
                    # old gfs 
                    #curl_command = 'curl "https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl?file=gfs.t'+dt_init.strftime('%H')+'z.pgrb2.0p25.f'+str(hr).zfill(3)+'&lev_mean_sea_level=on&lev_surface=on&var_PRES=on&var_PRMSL=on&subregion=&leftlon=-160&rightlon=-110&toplat=50&bottomlat=25&dir=%2F'+url_folder_str1+'%2F'+url_folder_str2+'" -o '+file_name_ingest
                    # new gfs 
                    curl_command = 'curl "https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl?file=gfs.t'+dt_init.strftime('%H')+'z.pgrb2.0p25.f'+str(hr).zfill(3)+'&lev_mean_sea_level=on&lev_surface=on&var_PRES=on&var_PRMSL=on&subregion=&leftlon=-160&rightlon=-110&toplat=50&bottomlat=25&dir=%2F'+url_folder_str1+'%2F'+url_folder_str2+'%2Fatmos''" -o '+file_name_ingest
                    #                      https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl?file=gfs.t12                        z.pgrb2.0p25.f000                 &lev_mean_sea_level=on&lev_surface=on&var_PRES=on&var_PRMSL=on&subregion=&leftlon=-160&rightlon=-110&toplat=50&bottomlat=25&dir=%2Fgfs.20210327       %2F12%2Fatmos
 
                #if model_name != 'gfs':
                print_curl_command = False
                if print_curl_command:
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
                 
        #if   (model_name == 'nam' and hr > 36):        
        #    hr += 3
        if   (model_name == 'gfs' and hr >= 120):        
            hr += 3
        else:
            hr += 1
    print      ('download_data end ')
    logger.info('download_data end ')

            
###############################################################################
def process_grib_data(dict_stn_metadata, model_name, dt_init, forecast_horizon_hr, bucket_name):

    print      ('process_grib_data begin ')
    logger.info('process_grib_data begin ')

    dir_init_temp = dt_init.strftime('%Y-%m-%d')
    dir_name_ingest    = os.path.join('data', 'ingest',    dir_init_temp)
    dir_name_processed = os.path.join('data', 'processed', dir_init_temp)
    
    # get list of files in ingest dir
    #file_list = glob.glob(os.path.join(dir_name_ingest, model_name+'*.grib2'))
    file_list = glob.glob(os.path.join(dir_name_ingest, model_name+'*'+dt_init.strftime('%Y-%m-%d_%H')+'*.grib2'))
    file_list.sort()
    n_files = len(file_list)
    print      ('  found %s files to process' %(n_files))
    logger.info('  found %s files to process' %(n_files))
    if n_files == 0:
        print      ('  no files to process')
        logger.info('  no files to process')
        return
        # sys.exit() 
        
    initial_read = False

    n = 0
    file_temp = file_list[0]
    for n, file_temp in enumerate(file_list): 
        
        print      ('    processing file %s of %s' %(n, n_files))
        logger.info('    processing file %s of %s' %(n, n_files))

        #file_name = os.path.dirname(file_temp)
        file_name = os.path.basename(file_temp)
        file_name_processed = os.path.join(dir_name_processed, file_name)

        try:
            ds_read = xr.open_dataset(file_temp, engine='cfgrib')        
        except Error as e:
            print      ('  ERROR reading %s ' %(e))
            logger.info('  ERROR reading %s ' %(e))
            os.system(temp_command)
            temp_command = 'rm -f '+file_temp    
            continue
        #except:
        #    print      ('  ERROR reading %s ' %(file_temp))
        #    logger.info('  ERROR reading %s ' %(file_temp))
            
        #sorted(ds_read.variables)
        # ds_sfc = xr.open_dataset(file_temp, engine='cfgrib',
        #      backend_kwargs={'filter_by_keys': {'typeOfLevel': 'surface'}})
        # ds_2m = xr.open_dataset(file_temp, engine='cfgrib',
        #       backend_kwargs={'filter_by_keys': {'typeOfLevel': 'heightAboveGround', 'level': 2}})
        # ds_10m = xr.open_dataset(file_temp, engine='cfgrib',
        #      backend_kwargs={'filter_by_keys': {'typeOfLevel': 'heightAboveGround', 'level': 10}})
        #sorted(ds_sfc.variables)
        
        # hrrr
        # sp
        # mslma
        # meanSea

        if not initial_read: 
            if model_name == 'hrrr' or model_name == 'nam':
                lon_2d = np.array(ds_read['longitude'])
                lon_2d = lon_2d - 360.0
                lat_2d = np.array(ds_read['latitude'])
            elif model_name == 'gfs':
                lon_1d = np.array(ds_read['longitude'])
                lon_1d = lon_1d - 360.0
                lat_1d = np.array(ds_read['latitude'])
                ny, nx = np.shape(lat_1d)[0], np.shape(lon_1d)[0]
                lon_2d = np.full([ny, nx], 0.0, dtype=float)
                lat_2d = np.full([ny, nx], 0.0, dtype=float)
                for i in range(0, nx):
                    lat_2d[:,i] = lat_1d
                for j in range(0, ny):
                    lon_2d[j,:] = lon_1d
            # hgt_2d = np.array(ds_sfc['orog'])
            # hgt_2d = hgt_2d*3.28084 # m to ft
            print('    lon_2d min max is %5.2f %5.2f ' %(np.nanmin(lon_2d), np.nanmax(lon_2d)))
            print('    lat_2d min max is %5.2f %5.2f ' %(np.nanmin(lat_2d), np.nanmax(lat_2d)))
            print_flag = True
            (j_loc_s, i_loc_s) = map_stn_locations_to_grid_locations(logger, dict_stn_metadata, lon_2d, lat_2d, print_flag)
            initial_read = True

        #dt_init = ds_read['time']
        dt_valid = ds_read['valid_time']
        
        if model_name == 'hrrr':
            p1_sfc_2d = ds_read['mslma']  # MSLP (MAPS System Reduction)
            p2_sfc_2d = ds_read['sp']  
            # mslma 
        elif model_name == 'nam' or model_name == 'gfs':
            p1_sfc_2d = ds_read['prmsl']
            p2_sfc_2d = ds_read['sp']
            #p2_sfc_2d = np.array(ds_read['sp'])

        # hrrr
        # mslma - Pressure reduced to MSL, # MSLP (MAPS System Reduction)
        # sp - surface pressure
        # meanSea - nothing
        
        # gfs and nam
        # prmsl - Pressure reduced to MSL
        # sp - surface pressure
        # meanSea - nothing            

        # units conversion hpa -> mb
        p1_sfc_2d = 0.01*p1_sfc_2d
        p2_sfc_2d = 0.01*p2_sfc_2d
        
        print_p_sfc_min_max = False
        if print_p_sfc_min_max:
            print('    p1_sfc_2d min max is %5.1f %5.1f ' %(np.nanmin(p1_sfc_2d), np.nanmax(p1_sfc_2d)))
            print('    p2_sfc_2d min max is %5.1f %5.1f ' %(np.nanmin(p2_sfc_2d), np.nanmax(p2_sfc_2d)))

        ds_read.close()
        del ds_read        

        # grab data at station location
        # does not work 
        #p1_sfc_stn = p1_sfc_2d[j_loc_s, i_loc_s]
        #np.shape(p1_sfc_stn)
        p1_sfc_stn = np.zeros([dict_stn_metadata['n_stn']], dtype=float)
        p2_sfc_stn = np.zeros([dict_stn_metadata['n_stn']], dtype=float)
        for s in range(0, dict_stn_metadata['n_stn']):
            p1_sfc_stn[s] = p1_sfc_2d[j_loc_s[s], i_loc_s[s]]
            p2_sfc_stn[s] = p2_sfc_2d[j_loc_s[s], i_loc_s[s]]

        #dir_ingest_stn = os.path.join('data/ingest/stn_csv')
        #if not os.path.isdir(dir_ingest_stn):
        #    temp_command = 'mkdir -p '+dir_ingest_stn
        #   print      ('    make new stn dir %s ' % (temp_command)) 
        #    logger.info('    make new stn dir %s ' % (temp_command)) 
        stn_file_name = os.path.join( dir_name_ingest , file_name.split('.')[0]+'.csv')
        print_stn_file_name = False
        if print_stn_file_name:
            print      ('    stn_file_name %s ' % (stn_file_name)) 
            logger.info('    stn_file_name %s ' % (stn_file_name)) 

        #print      ('    write p_sfc begin ')
        #logger.info('    write p_sfc begin ')
        column_str = ['stn_id', 'p1', 'p2']
        p_sfc_data = [dict_stn_metadata['stn_id'], p1_sfc_stn, p2_sfc_stn]
        #stn_info_transpose = np.transpose(stn_info) 
        p_sfc_df = pd.DataFrame(np.transpose(p_sfc_data), columns=column_str) 
        #stn_info_df = stn_info_df.sort_values(by='stn_mnet_id') 
        # stn_info_df = stn_info_df.sort_values(by='stn_name') 
        p_sfc_df.to_csv(stn_file_name) 
        #print      ('    write p_sfc end ')   
        #logger.info('    write p_sfc end ')   

        # archive raw grib file 
        temp_command = 'mv -f '+file_temp+' '+file_name_processed
        print_archive_output = False
        if print_archive_output:
            print      ('    archive output %s ' % (temp_command)) 
            logger.info('    archive output %s ' % (temp_command)) 
        os.system(temp_command)
        #print      ('    archive output: success ' ) 
        #logger.info('    archive_output: success ' ) 
        
    # clean up idx files
    temp_command = 'rm -f '+dir_name_ingest+'/*.idx'    
    print      ('  clean up idx files ') 
    logger.info('  clean up idx files ') 
    os.system(temp_command)
    print      ('process_grib_data end ')
    logger.info('process_grib_data end ')


###############################################################################
def process_csv_data(dict_stn_metadata, model_name, dt_init, forecast_horizon_hr, bucket_name):

    print      ('process_csv begin ')
    logger.info('process_csv begin ')


    dir_init_temp = dt_init.strftime('%Y-%m-%d')
    dir_name_ingest    = os.path.join('data', 'ingest',    dir_init_temp)
    dir_name_processed = os.path.join('data', 'processed', dir_init_temp)
    
    # get list of files in ingest dir
    #file_list = glob.glob(os.path.join(dir_name_ingest, model_name+'*.csv'))
    file_list = glob.glob(os.path.join(dir_name_ingest, model_name+'*'+dt_init.strftime('%Y-%m-%d_%H')+'*.csv'))
    file_list.sort()
    n_files = len(file_list)
    print      ('  found %s files to process' %(n_files))
    logger.info('  found %s files to process' %(n_files))
    if n_files == 0:
        print      ('  no files to process')
        logger.info('  no files to process')
        return
        # sys.exit() 

    # read or create master p_sfc file     
    p_sfc1_master_file = os.path.join(dir_name_processed, 'p_sfc1_'+model_name+'_'+dt_init.strftime('%Y-%m-%d_%H')+'_t_all.csv')
    p_sfc2_master_file = os.path.join(dir_name_processed, 'p_sfc2_'+model_name+'_'+dt_init.strftime('%Y-%m-%d_%H')+'_t_all.csv')
    if os.path.isfile(p_sfc1_master_file): # read master
        p_sfc1_hr_s_df = pd.read_csv(p_sfc1_master_file, index_col=0)
        p_sfc1_hr_s = p_sfc1_hr_s_df.values
        p_sfc2_hr_s_df = pd.read_csv(p_sfc2_master_file, index_col=0)
        p_sfc2_hr_s = p_sfc2_hr_s_df.values
        dt_axis = p_sfc1_hr_s_df.index.values
        # np.shape(p_sfc1_hr_s)
    else: # aggregate file does not exist 
        p_sfc1_hr_s = np.full([forecast_horizon_hr, dict_stn_metadata['n_stn']], np.nan, dtype=object)
        p_sfc2_hr_s = np.full([forecast_horizon_hr, dict_stn_metadata['n_stn']], np.nan, dtype=object)
        dt_axis = np.full([forecast_horizon_hr], None, dtype=object)
        for hr in range(0, forecast_horizon_hr):
            dt_axis[hr] = dt_init + td(hours=hr)
        # dt_axis1 = [dt_init + td(hours=hr) for hr in range(0, forecast_horizon_hr)]

    file_temp = file_list[0]
    for n, file_temp in enumerate(file_list): 
        #print      ('    processing file %s of %s, %s' %(n, n_files, file_temp))
        #logger.info('    processing file %s of %s, %s' %(n, n_files, file_temp))
        #file_name = os.path.dirname(file_temp)
        file_name = os.path.basename(file_temp)
        file_name_processed = os.path.join(dir_name_processed, file_name)

        # read csv
        p_sfc_df = pd.read_csv(file_temp, index_col=0)
        # calc hr from forecast_horizon in model name
        # find correct place in csv
        # need to verify works for gfs and nam
        hr = int(file_name.split('.')[0].split('_')[-1])
        # dont need stn_id, should automatically line up    
        stn_id = p_sfc_df['stn_id'].values
        #p_sfc1 = p_sfc_df['p_sfc1'].values
        #p_sfc2 = p_sfc_df['p_sfc2'].values
        p_sfc1 = p_sfc_df['p1'].values
        p_sfc2 = p_sfc_df['p2'].values
        # can combine above and below steps 
        p_sfc1_hr_s[hr,:] = p_sfc1
        p_sfc2_hr_s[hr,:] = p_sfc2
        
    # write to master csv
    print      ('  write p_sfc master begin ')
    logger.info('  write p_sfc master begin ')
    p_sfc1_hr_s_df = pd.DataFrame(p_sfc1_hr_s, index=dt_axis, columns=dict_stn_metadata['stn_id']) 
    p_sfc1_hr_s_df.to_csv(p_sfc1_master_file) 
    p_sfc2_hr_s_df = pd.DataFrame(p_sfc2_hr_s, index=dt_axis, columns=dict_stn_metadata['stn_id']) 
    p_sfc2_hr_s_df.to_csv(p_sfc2_master_file) 
    print      ('  write p_sfc master end ')   
    logger.info('  write p_sfc master end ')   

    print      ('  p_sfc1_hr_s min max is %5.1f %5.1f ' %(np.nanmin(p_sfc1_hr_s), np.nanmax(p_sfc1_hr_s)))
    logger.info('  p_sfc1_hr_s min max is %5.1f %5.1f ' %(np.nanmin(p_sfc1_hr_s), np.nanmax(p_sfc1_hr_s)))
    print      ('  p_sfc2_hr_s min max is %5.1f %5.1f ' %(np.nanmin(p_sfc2_hr_s), np.nanmax(p_sfc2_hr_s)))
    logger.info('  p_sfc2_hr_s min max is %5.1f %5.1f ' %(np.nanmin(p_sfc2_hr_s), np.nanmax(p_sfc2_hr_s)))

    # archive csv ingest file to processed
    print      ('  archive output begin' ) 
    logger.info('  archive_output begin' ) 
    for file_temp in file_list: 
        #file_name = os.path.dirname(file_temp)
        file_name = os.path.basename(file_temp)
        file_name_processed = os.path.join(dir_name_processed, file_name)
        temp_command = 'mv -f '+file_temp+' '+file_name_processed
        print_archive_output = False
        if print_archive_output:
            print      ('    archive output %s ' % (temp_command)) 
            logger.info('    archive output %s ' % (temp_command)) 
        os.system(temp_command)
        #print      ('    archive output: success ' ) 
        #logger.info('    archive_output: success ' ) 
    print      ('process_csv end ')
    logger.info('process_csv end ')


###############################################################################
def calc_pgrad(dict_stn_metadata, stn_id_pair_list_to_plot, model_name, dt_init, bucket_name):

    print      ('calc_pgrad begin ')
    logger.info('calc_pgrad begin ')

    dir_init_temp = dt_init.strftime('%Y-%m-%d')
    dir_name_ingest    = os.path.join('data', 'ingest',    dir_init_temp)
    dir_name_processed = os.path.join('data', 'processed', dir_init_temp)

    #model_name = 'hrrr'
    #for model_name in model_name_list:
    print      ('    processing %s ' %(model_name))
    logger.info('    processing %s ' %(model_name))
    # read p_sfc file     
    p_sfc1_master_file = os.path.join(dir_name_processed, 'p_sfc1_'+model_name+'_'+dt_init.strftime('%Y-%m-%d_%H')+'_t_all.csv')
    p_sfc2_master_file = os.path.join(dir_name_processed, 'p_sfc2_'+model_name+'_'+dt_init.strftime('%Y-%m-%d_%H')+'_t_all.csv')
    p_sfc1_diff_master_file = os.path.join(dir_name_processed, 'p_sfc1_diff_'+model_name+'_'+dt_init.strftime('%Y-%m-%d_%H')+'_t_all.csv')
    p_sfc2_diff_master_file = os.path.join(dir_name_processed, 'p_sfc2_diff_'+model_name+'_'+dt_init.strftime('%Y-%m-%d_%H')+'_t_all.csv')
    print      ('    input  file is %s ' %(p_sfc1_master_file))
    logger.info('    input  file is %s ' %(p_sfc1_master_file))
    print      ('    output file is %s ' %(p_sfc1_diff_master_file))
    logger.info('    output file is %s ' %(p_sfc1_diff_master_file))
    if not os.path.isfile(p_sfc1_master_file): 
        print      ('    ERROR - input file not found %s ' %(p_sfc1_master_file))
        logger.info('    ERROR - input file not found %s ' %(p_sfc1_master_file))
    else:
        # read master
        p_sfc1_hr_s_df = pd.read_csv(p_sfc1_master_file, index_col=0)
        #p_sfc1_hr_s = p_sfc1_hr_s_df.values
        p_sfc2_hr_s_df = pd.read_csv(p_sfc2_master_file, index_col=0)
        #p_sfc2_hr_s = p_sfc2_hr_s_df.values
        dt_axis = p_sfc1_hr_s_df.index.values
        forecast_horizon_hr = len(dt_axis)
        n_stn_pair = len(stn_id_pair_list_to_plot)
        p_sfc1_diff_hr_s = np.full([forecast_horizon_hr, n_stn_pair], np.nan, dtype=float)
        p_sfc2_diff_hr_s = np.full([forecast_horizon_hr, n_stn_pair], np.nan, dtype=float)
        s1 = 3
        s2 = 5
        print      ('    calculating pressure difference station pairs')
        logger.info('    calculating pressure difference station pairs')

        stn_id_pair = stn_id_pair_list_to_plot[0]
        for s, stn_id_pair in enumerate(stn_id_pair_list_to_plot):
            stn_id1, stn_id2 = stn_id_pair.split('-')[0], stn_id_pair.split('-')[1]
            s_id1 = list(dict_stn_metadata['stn_id']).index(stn_id1)
            s_id2 = list(dict_stn_metadata['stn_id']).index(stn_id2)
            p_sfc1_diff_hr_s[:,s] = p_sfc1_hr_s_df[dict_stn_metadata['stn_id'][s_id1]] - p_sfc1_hr_s_df[dict_stn_metadata['stn_id'][s_id2]]
            p_sfc2_diff_hr_s[:,s] = p_sfc2_hr_s_df[dict_stn_metadata['stn_id'][s_id1]] - p_sfc2_hr_s_df[dict_stn_metadata['stn_id'][s_id2]]
            #column_str[s1*dict_stn_metadata['n_stn']+s2] = dict_stn_metadata['stn_id'][s1]+'-'+dict_stn_metadata['stn_id'][s2]
                
        # write to master csv
        print      ('    write p_sfc_diff master begin ')
        logger.info('    write p_sfc_diff master begin ')
        p_sfc1_diff_hr_s_df = pd.DataFrame(p_sfc1_diff_hr_s, index=dt_axis, columns=stn_id_pair_list_to_plot).round(2) 
        #p_sfc1_diff_hr_s_df = p_sfc1_diff_hr_s_df.round(2)
        p_sfc1_diff_hr_s_df.to_csv(p_sfc1_diff_master_file) 
        p_sfc2_diff_hr_s_df = pd.DataFrame(p_sfc2_diff_hr_s, index=dt_axis, columns=stn_id_pair_list_to_plot).round(2) 
        p_sfc2_diff_hr_s_df.to_csv(p_sfc2_diff_master_file) 
        print      ('    write p_sfc_diff master end ')   
        logger.info('    write p_sfc_diff master end ')   
        
        print      ('    p_sfc1_diff_hr_s min max is %5.1f %5.1f ' %(np.nanmin(p_sfc1_diff_hr_s), np.nanmax(p_sfc1_diff_hr_s)))
        logger.info('    p_sfc1_diff_hr_s min max is %5.1f %5.1f ' %(np.nanmin(p_sfc1_diff_hr_s), np.nanmax(p_sfc1_diff_hr_s)))
        print      ('    p_sfc2_diff_hr_s min max is %5.1f %5.1f ' %(np.nanmin(p_sfc2_diff_hr_s), np.nanmax(p_sfc2_diff_hr_s)))
        logger.info('    p_sfc2_diff_hr_s min max is %5.1f %5.1f ' %(np.nanmin(p_sfc2_diff_hr_s), np.nanmax(p_sfc2_diff_hr_s)))
    
    print      ('calc_pgrad end ')
    logger.info('calc_pgrad end ')


###############################################################################
def plot_data(dict_stn_metadata, model_name_list, dt_init_expected, forecast_horizon_hr,  dt_start_lt, utc_conversion, time_zone_label, stn_id_pair_list_to_plot, bucket_name):
     
    print      ('open connection to mongo ')
    logger.info('open connection to mongo ')
    # open connection to mongo and connect to the db_connection
    mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")
    mongo_db = mongo_client.models_avail
    coll = mongo_db.models_avail
    #mongo_client =          MongoClient('mongodb://localhost:27017')
    #mongo_client = MongoClient()
    #mongo_client = MongoClient('localhost', 27017)
    # list db names
    # print(mongo_client.list_database_names())
    # list collection names
    # print(mongo_db.list_collection_names())
    
    # connect to the db collection 
    #mongo_db = mongo_client['models_avail']
    #collection = mongo_db['models_avail']
    # drop collection
    # coll.drop()
    # drop a db
    # mongo_db.drop()
    
    print      ('plot_data begin ')
    logger.info('plot_data begin ')
    warnings.filterwarnings("ignore") 
    dir_images = os.path.join('images', 'archive')
    if not os.path.isdir(dir_images):
        os.system('mkdir -p '+dir_images)

    n_stn_pair = len(stn_id_pair_list_to_plot)
    p_sfc1_diff_init_m_hr_s = np.full([5, 3, forecast_horizon_hr, n_stn_pair], np.nan, dtype=float)
    np.shape(p_sfc1_diff_init_m_hr_s)   
    p_sfc2_diff_init_m_hr_s = np.full([5, 3, forecast_horizon_hr, n_stn_pair], np.nan, dtype=float)
    dt_axis_utc_init = np.full([5, forecast_horizon_hr], np.nan, dtype=object)
    dt_axis_lt_init  = np.full([5, forecast_horizon_hr], np.nan, dtype=object)
    dt_init_count = 0
    dt_init = dt_init_expected - td(hours=24)
    dt_init_list = []
    # dt_init = dt_init_expected
    while dt_init <= dt_init_expected:
        print      ('    processing %s dt_init %s ' %(dt_init_count, dt_init.strftime('%Y-%m-%d_%H')))
        logger.info('    processing %s dt_init %s ' %(dt_init_count, dt_init.strftime('%Y-%m-%d_%H')))
        dt_init_list.append(dt_init)
        #dt_init += td(hours=update_frequency_hrs)
        # dt_init_count += 1        
        dir_init_temp = dt_init.strftime('%Y-%m-%d')
        dir_name_ingest    = os.path.join('data', 'ingest',    dir_init_temp)
        dir_name_processed = os.path.join('data', 'processed', dir_init_temp)

        model_name = 'gfs'
        m = 0
        for m, model_name in enumerate(model_name_list):
            print      ('      processing %s %s ' %(m, model_name))
            logger.info('      processing %s %s ' %(m, model_name))
            # read p_sfc_diff file     
            p_sfc1_diff_master_file = os.path.join(dir_name_processed, 'p_sfc1_diff_'+model_name+'_'+dt_init.strftime('%Y-%m-%d_%H')+'_t_all.csv')
            p_sfc2_diff_master_file = os.path.join(dir_name_processed, 'p_sfc2_diff_'+model_name+'_'+dt_init.strftime('%Y-%m-%d_%H')+'_t_all.csv')
            if not os.path.isfile(p_sfc1_diff_master_file): 
                print      ('      ERROR - input file not found %s ' %(p_sfc1_diff_master_file))
                logger.info('      ERROR - input file not found %s ' %(p_sfc1_diff_master_file))
            else:
                print      ('        input file exists ')
                logger.info('        input file exists ')
                # read master
                p_sfc1_diff_hr_s_df = pd.read_csv(p_sfc1_diff_master_file, index_col=0)
                p_sfc1_diff_hr_s = p_sfc1_diff_hr_s_df.values
                p_sfc2_diff_hr_s_df = pd.read_csv(p_sfc2_diff_master_file, index_col=0)
                p_sfc2_diff_hr_s = p_sfc2_diff_hr_s_df.values
                #dt_axis = p_sfc1_diff_hr_s_df.index.values
                dt_axis_utc = pd.to_datetime(p_sfc1_diff_hr_s_df.index) 
                dt_axis_lt  = pd.to_datetime(p_sfc1_diff_hr_s_df.index) - td(hours=utc_conversion)
                                
                #forecast_horizon_hr_temp = len(dt_axis_utc)
                #stn_id_pair_list = list(p_sfc1_diff_hr_s_df)
                # np.shape(p_sfc1_diff_hr_s_df)
                # np.shape(p_sfc1_diff_init_hr_s)
                n_hrs_found = len(dt_axis_utc)
                p_sfc1_diff_init_m_hr_s[dt_init_count, m, 0:n_hrs_found, :] = p_sfc1_diff_hr_s
                p_sfc2_diff_init_m_hr_s[dt_init_count, m, 0:n_hrs_found, :] = p_sfc2_diff_hr_s
                if (model_name == 'gfs'):
                    dt_axis_utc_init[dt_init_count,:] = dt_axis_utc
                    dt_axis_lt_init [dt_init_count,:] = dt_axis_lt

                # query mongodb to see if it exists
                try: 
                    result = coll.find_one({'model':model_name, 'dt_init':dt_init})
                    # print(result)
                    #n_results = len(result)
                    # if (n_results == 0): # no existing entry 
                    if not result: # no existing entry 
                        #data = {"model": model_name,
                        #        "dt_init": dt_init, 
                        #        "hrs_avail": n_hrs_found,
                        #        "dt_proc_lt": dt_start_lt.strftime('%Y-%m-%d_%H-%M')}
                        data = {"model": model_name,
                                "dt_init": dt_init, 
                                "hrs_avail": n_hrs_found,
                                "dt_proc_lt": dt_start_lt}
                        # result = coll.insert_one({"model": model_name, "dt_init": dt_init, "hrs_avail": n_hrs_found})
                        result = coll.insert_one(data)
                        print      ('        inserting new data ')
                        logger.info('        inserting new data ')
                    else: # update existing query 
                        n_hrs_prev = result['hrs_avail']
                        if n_hrs_found > n_hrs_prev:
                            #coll.update_one({'model':model_name, 
                            #                 'dt_init':dt_init},
                            #                {"$set":{"hrs_avail":n_hrs_found, "dt_proc_lt": dt_start_lt.strftime('%Y-%m-%d_%H-%M')}})
                            coll.update_one({'model':model_name, 
                                             'dt_init':dt_init},
                                            {"$set":{"hrs_avail":n_hrs_found, "dt_proc_lt": dt_start_lt}})
                            print      ('        updating new data ')
                            logger.info('        updating new data ')    
                        else: 
                            print      ('        no new data to update')
                            logger.info('        no new data to update')
                except:
                    pass
                  
        dt_init += td(hours=update_frequency_hrs)
        dt_init_count += 1        

    print      ('  read data end, begin plot data ')
    logger.info('  read data end, begin plot data ')
    
    color_list = ['r', 'b', 'g', 'c', 'm', 'y', 'k']    
    #n_days_list = [2, 4, 10]
    #n_days_list = [2, 3, 10]
    n_days_list = [2, 3, 8]
    figsize_x, figsize_y = 10, 5
    size_font = 14
    
    print      ('  set y-axis limits')
    logger.info('  set y-axis limits')
    y_axis_cache = {}
    #n_stn_pair = len(stn_id_pair_list_to_plot)
    for s,stn_id_pair in enumerate(stn_id_pair_list_to_plot):
        #if stn_id_pair == 'KWMC-KSAC':
        #if stn_id_pair in stn_id_pair_list_to_plot:
        y_axis_cache[stn_id_pair] = [-20, 20, 5]
    y_axis_cache['KACV-KSFO'] = [-2, 12, 2]
    y_axis_cache['KBFL-KSBA'] = [-10, 10, 2]
    y_axis_cache['KDAG-KLAX'] = [-2, 12, 2]
    y_axis_cache['KMFR-KRDD'] = [-2, 12, 2]
    y_axis_cache['KMFR-KSAC'] = [-4, 20, 4]
    y_axis_cache['KMFR-KSFO'] = [-4, 20, 4]
    y_axis_cache['KRDD-KSAC'] = [-2, 12, 2]
    y_axis_cache['KSMX-KSBA'] = [-6, 6, 1]
    y_axis_cache['KWMC-KSAC'] = [-4, 20, 4]
    y_axis_cache['KWMC-KSFO'] = [-5, 25, 5]
     
    print      ('  dt_init_list is ' )
    logger.info('  dt_init_list is ' )
    
    # find most recent full forecast 
    max_hrs_found = 0
    i_most_recent = 0
    m = 0 # check gfs
    s = stn_id_pair_list_to_plot.index('KWMC-KSAC')
    for i, dt_init in enumerate(dt_init_list):
         mask = ~np.isnan(p_sfc1_diff_init_m_hr_s[i,m,:,s])
         hrs_found = len(p_sfc1_diff_init_m_hr_s[i,m,mask,s])
         print      ('    %s, hrs found %s ' %(dt_init, hrs_found))
         logger.info('    %s, hrs found %s ' %(dt_init, hrs_found))
         if hrs_found >= max_hrs_found:
             i_most_recent = i
             max_hrs_found = hrs_found
             #print(i, hrs_found)
    # i_most_recent -= 1
    print      ('  using most recent full init %s %s ' %(i, dt_init_list[i_most_recent].strftime('%Y-%m-%d_%H-%M')))
    logger.info('  using most recent full init %s %s ' %(i, dt_init_list[i_most_recent].strftime('%Y-%m-%d_%H-%M')))
 
    # shorten data to valid dt_init only
    p_sfc1_diff_init_m_hr_s = p_sfc1_diff_init_m_hr_s[0:i_most_recent+1,:,:,:]
    p_sfc2_diff_init_m_hr_s = p_sfc2_diff_init_m_hr_s[0:i_most_recent+1,:,:,:]
    dt_init_list = dt_init_list[0:i_most_recent+1]
    dt_axis_lt_init = dt_axis_lt_init[0:i_most_recent+1,:]
    n_init = len(dt_init_list)

    # np.shape(p_sfc1_diff_init_m_hr_s)

    ######################################
    # latest init, all models
    print      ('  plot latest init, all models ')
    logger.info('  plot latest init, all models ')
    stn_id_pair = 'KWMC-KSAC'
    s = stn_id_pair_list_to_plot.index('KWMC-KSAC')
    # note csmith - i_most_recent is off by one ? 
    i = i_most_recent
    dt_init_list[i]
    model_name = 'gfs'
    m = 0
    d, n_days = 0, 2    
    #d, n_days = 1, 3    
    #d, n_days = 2, 10    
    for s,stn_id_pair in enumerate(stn_id_pair_list_to_plot):
        #if stn_id_pair == 'KWMC-KSAC':
        if stn_id_pair in stn_id_pair_list_to_plot:
            print      ('    plotting %s %s ' %(s, stn_id_pair))
            logger.info('    plotting %s %s ' %(s, stn_id_pair))
            for d, n_days in enumerate(n_days_list):

                dt_min_plot = dt(dt_axis_lt_init[i,0].year, dt_axis_lt_init[i,0].month, dt_axis_lt_init[i,0].day, 0, 0, 0)
                #dt_max_plot = dt_min_plot + td(days=n_days+1)
                dt_max_plot = dt_min_plot + td(days=n_days)
                if   n_days == 2:
                    delta_ticks = td(hours=12)
                    dt_format = '%m/%d %H'
                elif n_days == 3:
                    delta_ticks = td(hours=12)
                    dt_format = '%m/%d %H'    
                elif n_days == 8:
                    delta_ticks = td(hours=24)
                    dt_format = '%m/%d'
                delta_lines = td(hours=24)
                # dt_max_plot = datetime_min_plot + datetime.timedelta(hours=24*8) # 14, 24  
                #datetick_format = '%H'    
                dt_ticks = drange(dt_min_plot, dt_max_plot+delta_ticks, delta_ticks)
                n_date_ticks = len(dt_ticks) 
                
                dt_newday_ticks = drange(dt_min_plot, dt_max_plot+td(hours=24), td(hours=24))
                dt_nighttime_ticks = drange(dt_min_plot-td(hours=6), dt_max_plot+td(hours=24), td(hours=24))
                alpha_night = 0.5
                
                [y_min, y_max, y_int] = y_axis_cache[stn_id_pair]
                # [y_min, y_max, y_int] = [-20, 20, 5]
                y_ticks = list(range(y_min, y_max+y_int, y_int))
                # n_days_plot = (dt_max_plot - dt_min_plot).days 
                
                
                fig_num = 133
                fig = plt.figure(num=fig_num,figsize=(figsize_x, figsize_y)) 
                plt.clf()
                m = 0
                model_name = 'gfs'
                for m, model_name in enumerate(model_name_list):
                    mask = ~np.isnan(p_sfc1_diff_init_m_hr_s[i,m,:,s])
                    plt.plot(dt_axis_lt_init[i,mask], p_sfc1_diff_init_m_hr_s[i,m,mask,s], color_list[m], linestyle='-', label=model_name.upper(), linewidth=3.0, marker='o', markersize=0, markeredgecolor='k') 
                    #plt.plot(dt_axis_lt_init[i,mask], p_sfc2_diff_init_m_hr_s[i,m,mask,s], color_list[m], linestyle='-', label=model_name, linewidth=3.0, marker='o', markersize=0, markeredgecolor='k') 
                #plt.plot(dt_axis_lt_init[i,:], p_sfc1_diff_init_m_hr_s[i,m,:,s], 'r', linestyle='-', label='obs ws', linewidth=2.0, marker='o', markersize=2, markeredgecolor='k') 
                plt.legend(loc=3,fontsize=size_font-2,ncol=1) 
                plt.plot([dt_start_lt, dt_start_lt], [y_min, y_max], 'y', linestyle='--', linewidth=1.0, marker='o', markersize=0, markeredgecolor='k') 
                plt.plot([dt_ticks[0], dt_ticks[-1]], [0.0, 0.0], 'k', linestyle='-', linewidth=2.0, marker='o', markersize=0, markeredgecolor='k') 
                for y_tick in y_ticks:
                    plt.plot([dt_ticks[0], dt_ticks[-1]], [y_tick, y_tick], 'gray', linestyle='-', linewidth=0.5, marker='o', markersize=0) 
                for dt_tick in dt_ticks:
                    plt.plot([dt_tick, dt_tick], [y_min, y_max], 'gray', linestyle='-', linewidth=0.5, marker='o', markersize=0) 
                for dt_tick in dt_newday_ticks:
                    plt.plot([dt_tick, dt_tick], [y_min, y_max], 'gray', linestyle='-', linewidth=1.0, marker='o', markersize=0) 
                if n_days < 8:
                    for dt_tick in dt_nighttime_ticks:
                        plt.axvspan(dt_tick, dt_tick+0.5, color='grey', alpha=alpha_night, linewidth=0)    
                plt.xlim([dt_ticks[0], dt_ticks[-1]])
                plt.gca().xaxis.set_major_formatter(DateFormatter(dt_format))
                plt.xticks(dt_ticks, visible=True, fontsize=size_font) 
                plt.yticks(y_ticks, fontsize=size_font)
                plt.ylim([y_min, y_max])
                plt.xlabel('date time ['+time_zone_label+']',fontsize=size_font,labelpad=00)
                plt.ylabel('$\Delta$ slp [mb]',fontsize=size_font,labelpad=20)
                plt.title('$\Delta$ slp %s, %s Z init, updated: %s %s ' % (stn_id_pair, dt_init_list[i].strftime('%Y-%m-%d_%H'), dt_start_lt.strftime('%Y-%m-%d_%H-%M'), time_zone_label), \
                  fontsize=size_font+2, x=0.5, y=1.01)                     
                plt.show() 
                #filename = 'del_slp_all_model_'+stn_id_pair+'_'+dt_init_list[i].strftime('%Y-%m-%d_%H')+'_'+str(n_days)+'.png' 
                filename = 'del_slp_all_model_'+stn_id_pair+'_current_'+str(n_days)+'.png' 
                plot_name = os.path.join('images', filename)
                plt.savefig(plot_name) 
                filename = 'del_slp_all_model_'+stn_id_pair+'_'+dt_init_list[i].strftime('%Y-%m-%d_%H')+'_'+str(n_days)+'_'+dt_start_lt.strftime('%Y-%m-%d_%H')+'_'+time_zone_label+'.png' 
                plot_name = os.path.join('images', 'archive', filename)
                plt.savefig(plot_name) 
                 
    ######################################
    # single model, last 4 inits
    print      ('  plot single model, all inits ')
    logger.info('  plot single model, all inits ')
    
    m, model_name = 0, 'gfs'
    m, model_name = 1, 'nam'
    m, model_name = 2, 'hrrr'
    for s,stn_id_pair in enumerate(stn_id_pair_list_to_plot):
        #if stn_id_pair == 'KWMC-KSAC':
        if stn_id_pair in stn_id_pair_list_to_plot:
            print      ('    plotting %s %s ' %(s, stn_id_pair))
            logger.info('    plotting %s %s ' %(s, stn_id_pair))
            for m, model_name in enumerate(model_name_list):
                for d, n_days in enumerate(n_days_list):
                    if (model_name == 'hrrr' and n_days == 2) or (model_name == 'nam' and n_days == 3) or (model_name == 'gfs' and n_days == 8):
                        #dt_min_plot = dt(dt_axis_lt_init[4,0].year, dt_axis_lt_init[4,0].month, dt_axis_lt_init[i,0].day, 0, 0, 0)
                        dt_min_plot = dt(dt_axis_lt_init[-1,0].year, dt_axis_lt_init[-1,0].month, dt_axis_lt_init[-1,0].day, 0, 0, 0)
                        #dt_max_plot = dt_min_plot + td(days=n_days+1)
                        dt_max_plot = dt_min_plot + td(days=n_days)
                        if   n_days == 2:
                            delta_ticks = td(hours=12)
                            dt_format = '%m/%d %H'
                        elif n_days == 3:
                            delta_ticks = td(hours=12)
                            dt_format = '%m/%d %H'    
                        elif n_days == 8:
                            delta_ticks = td(hours=24)
                            dt_format = '%m/%d'
                        delta_lines = td(hours=24)
                        # dt_max_plot = datetime_min_plot + datetime.timedelta(hours=24*8) # 14, 24  
                        #datetick_format = '%H'    
                        dt_ticks = drange(dt_min_plot, dt_max_plot+delta_ticks, delta_ticks)
                        n_date_ticks = len(dt_ticks) 
                        
                        dt_newday_ticks = drange(dt_min_plot, dt_max_plot+td(hours=24), td(hours=24))
                        dt_nighttime_ticks = drange(dt_min_plot-td(hours=6), dt_max_plot+td(hours=24), td(hours=24))
                        alpha_night = 0.5
                        
                        [y_min, y_max, y_int] = y_axis_cache[stn_id_pair]
                        # [y_min, y_max, y_int] = [-20, 20, 5]
                        y_ticks = list(range(y_min, y_max+y_int, y_int))
                        # n_days_plot = (dt_max_plot - dt_min_plot).days 
                        
                        
                        fig_num = 134
                        fig = plt.figure(num=fig_num,figsize=(figsize_x, figsize_y)) 
                        plt.clf()
                        i = n_init-1
                        #for i, dt_init in enumerate(dt_init_list[::-1]):
                        while i >= 0:
                            #print(dt_init_list[i])
                            mask = ~np.isnan(p_sfc1_diff_init_m_hr_s[i,m,:,s])
                            plt.plot(dt_axis_lt_init[i,mask], p_sfc1_diff_init_m_hr_s[i,m,mask,s], color_list[i], linestyle='-', label=dt_init_list[i].strftime('%Y-%m-%d_%H'), linewidth=3.0, marker='o', markersize=0, markeredgecolor='k') 
                            i -=1 
                            #plt.plot(dt_axis_lt_init[i,mask], p_sfc2_diff_init_m_hr_s[i,m,mask,s], color_list[m], linestyle='-', label=model_name, linewidth=3.0, marker='o', markersize=0, markeredgecolor='k') 
                        #plt.plot(dt_axis_lt_init[i,:], p_sfc1_diff_init_m_hr_s[i,m,:,s], 'r', linestyle='-', label='obs ws', linewidth=2.0, marker='o', markersize=2, markeredgecolor='k') 
                        plt.legend(loc=3,fontsize=size_font-2,ncol=1) 
                        plt.plot([dt_start_lt, dt_start_lt], [y_min, y_max], 'y', linestyle='--', linewidth=1.0, marker='o', markersize=0, markeredgecolor='k') 
                        plt.plot([dt_ticks[0], dt_ticks[-1]], [0.0, 0.0], 'k', linestyle='-', linewidth=2.0, marker='o', markersize=0, markeredgecolor='k') 
                        for y_tick in y_ticks:
                            plt.plot([dt_ticks[0], dt_ticks[-1]], [y_tick, y_tick], 'gray', linestyle='-', linewidth=0.5, marker='o', markersize=0) 
                        for dt_tick in dt_ticks:
                            plt.plot([dt_tick, dt_tick], [y_min, y_max], 'gray', linestyle='-', linewidth=0.5, marker='o', markersize=0) 
                        for dt_tick in dt_newday_ticks:
                            plt.plot([dt_tick, dt_tick], [y_min, y_max], 'gray', linestyle='-', linewidth=1.0, marker='o', markersize=0) 
                        if n_days < 8:
                            for dt_tick in dt_nighttime_ticks:
                                plt.axvspan(dt_tick, dt_tick+0.5, color='grey', alpha=alpha_night, linewidth=0)    
                        plt.xlim([dt_ticks[0], dt_ticks[-1]])
                        plt.gca().xaxis.set_major_formatter(DateFormatter(dt_format))
                        plt.xticks(dt_ticks, visible=True, fontsize=size_font) 
                        plt.yticks(y_ticks, fontsize=size_font)
                        plt.ylim([y_min, y_max])
                        plt.xlabel('date time ['+time_zone_label+']',fontsize=size_font,labelpad=00)
                        plt.ylabel('$\Delta$ slp [mb]',fontsize=size_font,labelpad=20)                      
                        plt.title('$\Delta$ slp %s, %s model, updated: %s %s' % (stn_id_pair, model_name.upper(), dt_start_lt.strftime('%Y-%m-%d_%H-%M'), time_zone_label), \
                          fontsize=size_font+2, x=0.5, y=1.01)                     
                        plt.show() 
                        filename = 'del_slp_all_init_'+stn_id_pair+'_'+model_name+'_'+str(n_days)+'.png' 
                        plot_name = os.path.join('images',filename)
                        plt.savefig(plot_name) 
                        filename = 'del_slp_all_init_'+stn_id_pair+'_'+model_name+'_'+str(n_days)+'_'+dt_start_lt.strftime('%Y-%m-%d_%H')+'_'+time_zone_label+'.png' 
                        plot_name = os.path.join('images', 'archive', filename)
                        plt.savefig(plot_name) 
        
    print      ('plot_data end ')
    logger.info('plot_data end ')


###############################################################################
def obs_historical_download(dict_stn_metadata, stn_list_to_use, utc_conversion, time_zone_label, bucket_name):

    print      ('obs_historical_download begin ')
    logger.info('obs_historical_download begin ')

    dir_sfc_obs_historical = os.path.join('data', 'sfc_obs_historical')
    if not os.path.isdir(dir_sfc_obs_historical):
        os.system('mkdir -p '+dir_sfc_obs_historical)

    mesowest_token = os.environ['mesowest_token']
    url_base = 'http://api.mesowest.net/v2/stations/timeseries?stid='
            
    s = 2 # KSAC
    s = 9 # KWMC
    
    # KSFO, KWMC, KDAG, KLAX 
    
    #for s in range(6,8,1): 
    #for s in range(0, dict_stn_metadata['n_stn']): 
    for s in [1, 4, 9, 10]:
        #if ('SJS' in dict_stn_metadata['stn_name'][s]):
        #if ('JBG' in dict_stn_metadata['stn_id'][s]):
        print      ('  processing s %s, s = %s of %s ' % (dict_stn_metadata['stn_id'][s], s, dict_stn_metadata['n_stn']))  
        logger.info('  processing s %s, s = %s of %s ' % (dict_stn_metadata['stn_id'][s], s, dict_stn_metadata['n_stn']))  
        #for d in range(0, n_days, 1):
        if (dict_stn_metadata['stn_id'][s] in stn_list_to_use):
            #yy = 2017 # 2017, 2018, 2019, 2020 done already 
            #while yy <= dt.utcnow().year:
            yy = 2000 # 2017, 2018, 2019, 2020 done already 
            while yy < 2017:
                #dt_start = dt(2020, 9, 25)
                #dt_end   = dt(2020, 9, 29)            
                dt_start = dt(yy, 1, 1)
                #dt_end   = dt(yy, 12, 31, 23, 59)
                dt_end   = min(dt(yy, 12, 31, 23, 59), dt.utcnow())
                print      ('    processing yy %s ' % (yy))
                logger.info('    processing yy %s ' % (yy))
                file_name_stn_write = os.path.join(dir_sfc_obs_historical, 'stn_obs_'+dict_stn_metadata['stn_id'][s]+'_'+str(yy)+'.csv') 
                if os.path.isfile(file_name_stn_write):
                    print      ('      skipping, file exists already')
                    logger.info('      skipping, file exists already')
                else:                
                    # url_temp = url_base+str(dict_stn_metadata['stn_id'][s])+'&start='+dt_temp.strftime('%Y%m%d0000')+'&end='+dt_temp.strftime('%Y%m%d2359')+'&token='+mesowest_token+'&obtimezone=utc'+'&timeformat=%Y-%m-%d_%H-%M' 
                    # url_temp = url_base+str(dict_stn_metadata['stn_id'][s])+'&start='+dt_start.strftime('%Y%m%d0000')+'&end='+dt_end.strftime('%Y%m%d2359')+'&token='+mesowest_token+'&obtimezone=utc'+'&timeformat=%Y-%m-%d_%H-%M' 
                    # slp and alt 
                    #url_temp = url_base+str(dict_stn_metadata['stn_id'][s])+'&start='+dt_start.strftime('%Y%m%d0000')+'&end='+dt_end.strftime('%Y%m%d2359')+'&vars=sea_level_pressure,altimeter&token='+mesowest_token+'&obtimezone=utc'+'&timeformat=%Y-%m-%d_%H-%M' 
                    # alt only
                    #url_temp = url_base+str(dict_stn_metadata['stn_id'][s])+'&start='+dt_start.strftime('%Y%m%d0000')+'&end='+dt_end.strftime('%Y%m%d2359')+'&vars=altimeter&token='+mesowest_token+'&obtimezone=utc'+'&timeformat=%Y-%m-%d_%H-%M' 
                    # slp only 
                    url_temp = url_base+str(dict_stn_metadata['stn_id'][s])+'&start='+dt_start.strftime('%Y%m%d0000')+'&end='+dt_end.strftime('%Y%m%d2359')+'&vars=sea_level_pressure&token='+mesowest_token+'&obtimezone=utc'+'&timeformat=%Y-%m-%d_%H-%M' 

                    # print(url_temp)
                    # NOTE CSMITH - need to filter to only variables needed - alt and slp yes, pres no
                    # &vars=air_temp,volt&token=YOUR_TOKEN_HERE        
                    # &vars=sea_level_pressure,altimeter&token=YOUR_TOKEN_HERE
                    print      ('    url_temp is %s ' % (url_temp))
                    logger.info('    url_temp is %s ' % (url_temp))
                    web_temp = requests.get(url_temp)
                    response  = web_temp.json() 
                    data_parse = response['STATION']
                    if (len(data_parse) == 0): # station contains no data 
                        print      ('    sensor_list empty')
                        logger.info('    sensor_list empty')
                    else: # (len(data_parse) > 0)
            
                        dt_read = np.array(response['STATION'][0]['OBSERVATIONS']['date_time']) # e.g. [u'2015-11-18T00:53:00Z', u'2015-11-18T01:53:00Z', ... u'2015-11-18T23:53:00Z'],
                        n_time_read = len(dt_read)
                        dt_obs_temp = []
                        n = 0 
                        for n in range(0,n_time_read,1): 
                            # dt_read_temp = dt.strptime(str(dt_read[n]),'%Y-%m-%dT%H:%M:%SZ')
                            dt_read_temp = dt.strptime(str(dt_read[n]),'%Y-%m-%d_%H-%M')
                            dt_obs_temp.append(dt_read_temp)
                            del dt_read_temp 
                        sensor_list = response['STATION'][0]['SENSOR_VARIABLES'] 
                        #print (sensor_list)
                
                        # temp 
                        if   ('air_temp' in sensor_list): 
                            temp_read = np.array(response['STATION'][0]['OBSERVATIONS']['air_temp_set_1'],dtype='float') 
                        else: 
                            temp_read = np.zeros([n_time_read])
                        # ws 
                        if   ('wind_speed' in sensor_list): 
                            ws_read = np.array(response['STATION'][0]['OBSERVATIONS']['wind_speed_set_1'],dtype='float') 
                        else: 
                            ws_read = np.zeros([n_time_read])
                        # wsg 
                        if   ('wind_gust' in sensor_list): 
                            wsg_read = np.array(response['STATION'][0]['OBSERVATIONS']['wind_gust_set_1'],dtype='float') 
                        else: 
                            wsg_read = np.zeros([n_time_read])
                        # wd             
                        if   ('wind_direction' in sensor_list): 
                            wd_read = np.array(response['STATION'][0]['OBSERVATIONS']['wind_direction_set_1'],dtype='float') 
                        else: 
                            wd_read = np.zeros([n_time_read])
                        if   ('relative_humidity' in sensor_list): 
                            rh_read = np.array(response['STATION'][0]['OBSERVATIONS']['relative_humidity_set_1'],dtype='float') 
                        else: 
                            rh_read = np.zeros([n_time_read])
                
                        if   ('sea_level_pressure' in sensor_list): 
                            slp_read = np.array(response['STATION'][0]['OBSERVATIONS']['sea_level_pressure_set_1d'],dtype='float')            
                        else: 
                            slp_read = np.zeros([n_time_read])
                
                        if   ('pressure' in sensor_list): 
                            pres_read = np.array(response['STATION'][0]['OBSERVATIONS']['pressure_set_1d'],dtype='float') 
                        else: 
                            pres_read = np.zeros([n_time_read])
                
                        if   ('altimeter' in sensor_list): 
                            alt_read = np.array(response['STATION'][0]['OBSERVATIONS']['altimeter_set_1'],dtype='float') 
                        else: 
                            alt_read = np.zeros([n_time_read])
                
                        # units conversion hpa -> mb
                        pres_read = 0.01*pres_read
                        alt_read  = 0.01*alt_read
                        slp_read  = 0.01*slp_read
                
                        #alt_read  = np.zeros([n_time_read])
                        #slp_read  = np.zeros([n_time_read])
                        u_ws_read = np.zeros([n_time_read])
                        v_ws_read = np.zeros([n_time_read])
                                    
                        # write the csv file - yes rh
                        stn_data = [temp_read, ws_read, wsg_read, wd_read, rh_read, slp_read, pres_read, alt_read]
                        stn_data = np.transpose(stn_data) 
                        stn_data_df = pd.DataFrame(stn_data, index=dt_obs_temp, columns=['temp','ws', 'wsg', 'wd', 'rh', 'slp', 'pres', 'alt']).round(2) 
                        #file_name_stn_write = os.path.join(dir_data_ingest, 'stn_obs_'+dict_stn_metadata['stn_id'][s]+'_'+dt_temp.strftime('%Y-%m-%d')+'.csv') 
                        stn_data_df.to_csv(file_name_stn_write) 
                  
                        ## change nan to NULL for compatability with postgres
                        ## temp 
                        #index_nan = ([np.isnan(temp_read)]) 
                        #temp_read = temp_read.astype(object)
                        #temp_read[index_nan] = 'NULL'
                        #del index_nan 
                
                yy += 1

    print      ('obs_historical_download end ')
    logger.info('obs_historical_download end ')

###############################################################################
def datematch_to_hourly(var_raw, dt_axis_raw, dt_axis_hr_lst, obs_window_minutes):
    # debugging    
    # var_raw = stn_read_df_f['slp'].values
    # dt_axis_raw = stn_read_df_f.index

    warnings.simplefilter('ignore', RuntimeWarning) # nanmean of all nan

    n_hrs = len(dt_axis_hr_lst)
    dummy_axis = np.arange(0, n_hrs) 
    dt_axis_hr_lst_df = pd.DataFrame(dummy_axis, index=dt_axis_hr_lst)
    nt = len(dt_axis_raw) 

    n_dims = np.ndim(var_raw) 
    if   (n_dims == 1): 
        [n_dim1] = np.shape(var_raw) 
        var_raw_df = pd.DataFrame(var_raw[:], index=dt_axis_raw)
        var_hr = np.full([n_hrs], np.nan, dtype='float')
    elif (n_dims == 2): 
        [n_dim1, n_dim2] = np.shape(var_raw) 
        var_raw_df = pd.DataFrame(var_raw[:,0], index=dt_axis_raw)
        var_hr = np.full([n_hrs, n_dim2], np.nan, dtype='float')
    elif (n_dims == 3): 
        [n_dim1, n_dim2, n_dim3] = np.shape(var_raw) 
        var_raw_df = pd.DataFrame(var_raw[:,0,0], index=dt_axis_raw)
        var_hr = np.full([n_hrs, n_dim2, n_dim3], np.nan, dtype='float')
    elif (n_dims == 4): 
        [n_dim1, n_dim2, n_dim3, n_dim4] = np.shape(var_raw) 
        var_raw_df = pd.DataFrame(var_raw[:,0,0,0], index=dt_axis_raw)
        var_hr = np.full([n_hrs, n_dim2, n_dim3, n_dim4], np.nan, dtype='float')
        
    # n = 100812
    for n in range(0, n_hrs, 1):  
        if (n%10000 == 0):
            print      ('      processing %s of %s' %(str(n).zfill(6), n_hrs))
            logger.info('      processing %s of %s' %(str(n).zfill(6), n_hrs))
        index_min = (var_raw_df.index <= dt_axis_hr_lst_df.index[n]-td(minutes=30)).argmin() 
        index_max = (var_raw_df.index <  dt_axis_hr_lst_df.index[n]+td(minutes=30)).argmin() 
        if (index_min < nt and index_max > 0):
            if (index_min != index_max):      
                index_diff = index_max-index_min
                #if (index_diff != 1 or (index_diff == 1 and not np.isnan(var_raw[index_min,0,0,0]))):                     
                if   (index_diff == 1): # only 1 data point found                 
                    if   (n_dims == 1): 
                        var_hr[n]       = var_raw[index_min] 
                    elif (n_dims == 2): 
                        var_hr[n,:]     = var_raw[index_min,:] 
                    elif (n_dims == 3): 
                        var_hr[n,:,:]   = var_raw[index_min,:,:] 
                    elif (n_dims == 4): 
                        var_hr[n,:,:,:] = var_raw[index_min,:,:,:]                
                elif (index_diff != 1): # more than one data point found 
                    if   (n_dims == 1): 
                        var_hr[n]       = np.nanmean(var_raw[index_min:index_max]) 
                    elif (n_dims == 2): 
                        #var_hr[n,:]     = np.nanmean(var_raw[index_min:index_max,:]) 
                        for n2 in range(0, n_dim2, 1):   
                            var_hr[n,n2] = np.nanmean(var_raw[index_min:index_max,n2]) 
                    elif (n_dims == 3): 
                        #var_hr[n,:,:]   = np.nanmean(var_raw[index_min:index_max,:,:]) 
                        for n2 in range(0, n_dim2, 1):   
                            for n3 in range(0, n_dim3, 1):   
                                  var_hr[n,n2,n3] = np.nanmean(var_raw[index_min:index_max,n2,n3]) 
                    elif (n_dims == 4): 
                        #var_hr[n,:,:,:] = np.nanmean(var_raw[index_min:index_max,:,:,:]) 
                        for n2 in range(0, n_dim2, 1):   
                            for n3 in range(0, n_dim3, 1):   
                                for n4 in range(0, n_dim4, 1):   
                                  var_hr[n,n2,n3,n4] = np.nanmean(var_raw[index_min:index_max,n2,n3,n4]) 
                del index_diff       
        # note csmith 2016/04/26 - add these two lines of code below for most recent data point 
        elif (index_min == nt-1 and index_max == 0): # right most data point 
            if   (n_dims == 1): 
                var_hr[n]       = np.nanmean(var_raw[index_min]) 
            elif (n_dims == 2): 
                #var_hr[n,:]     = np.nanmean(var_raw[index_min,:]) 
                for n2 in range(0, n_dim2, 1):   
                    var_hr[n,n2] = np.nanmean(var_raw[index_min,n2]) 
            elif (n_dims == 3): 
                #var_hr[n,:,:]   = np.nanmean(var_raw[index_min,:,:]) 
                for n2 in range(0, n_dim2, 1):   
                    for n3 in range(0, n_dim3, 1):   
                        var_hr[n,n2,n3] = np.nanmean(var_raw[index_min,n2,n3]) 
            elif (n_dims == 4): 
                #var_hr[n,:,:,:] = np.nanmean(var_raw[index_min,:,:,:]) 
                for n2 in range(0, n_dim2, 1):   
                    for n3 in range(0, n_dim3, 1):   
                        for n4 in range(0, n_dim4, 1):   
                          var_hr[n,n2,n3,n4] = np.nanmean(var_raw[index_min,n2,n3,n4])
        del index_min, index_max  

    return var_hr  

###############################################################################
def datematch_to_5min(var_raw, dt_axis_raw, dt_axis_5min_lst, obs_window_minutes):
    # debugging    
    # var_raw = stn_read_df_f['slp'].values
    # dt_axis_raw = stn_read_df_f.index

    warnings.simplefilter('ignore', RuntimeWarning) # nanmean of all nan

    n_5min = len(dt_axis_5min_lst)
    dummy_axis = np.arange(0, n_5min) 
    dt_axis_5min_lst_df = pd.DataFrame(dummy_axis, index=dt_axis_5min_lst)
    nt = len(dt_axis_raw) 

    n_dims = np.ndim(var_raw) 
    if   (n_dims == 1): 
        [n_dim1] = np.shape(var_raw) 
        var_raw_df = pd.DataFrame(var_raw[:], index=dt_axis_raw)
        var_5min = np.full([n_5min], np.nan, dtype='float')
    elif (n_dims == 2): 
        [n_dim1, n_dim2] = np.shape(var_raw) 
        var_raw_df = pd.DataFrame(var_raw[:,0], index=dt_axis_raw)
        var_5min = np.full([n_5min, n_dim2], np.nan, dtype='float')
    elif (n_dims == 3): 
        [n_dim1, n_dim2, n_dim3] = np.shape(var_raw) 
        var_raw_df = pd.DataFrame(var_raw[:,0,0], index=dt_axis_raw)
        var_5min = np.full([n_5min, n_dim2, n_dim3], np.nan, dtype='float')
    elif (n_dims == 4): 
        [n_dim1, n_dim2, n_dim3, n_dim4] = np.shape(var_raw) 
        var_raw_df = pd.DataFrame(var_raw[:,0,0,0], index=dt_axis_raw)
        var_5min = np.full([n_5min, n_dim2, n_dim3, n_dim4], np.nan, dtype='float')
        
    # n = 100812
    for n in range(0, n_5min, 1):  
        if (n%10000 == 0):
            print      ('      processing %s of %s' %(str(n).zfill(7), str(n_5min).zfill(7)))
            logger.info('      processing %s of %s' %(str(n).zfill(7), str(n_5min).zfill(7)))
        index_min = (var_raw_df.index <= dt_axis_5min_lst_df.index[n]-td(minutes=2)).argmin() 
        index_max = (var_raw_df.index <= dt_axis_5min_lst_df.index[n]+td(minutes=2)).argmin() 
        if (index_min < nt and index_max > 0):
            if (index_min != index_max):      
                index_diff = index_max-index_min
                #if (index_diff != 1 or (index_diff == 1 and not np.isnan(var_raw[index_min,0,0,0]))):                     
                if   (index_diff == 1): # only 1 data point found                 
                    if   (n_dims == 1): 
                        var_5min[n]       = var_raw[index_min] 
                    elif (n_dims == 2): 
                        var_5min[n,:]     = var_raw[index_min,:] 
                    elif (n_dims == 3): 
                        var_5min[n,:,:]   = var_raw[index_min,:,:] 
                    elif (n_dims == 4): 
                        var_5min[n,:,:,:] = var_raw[index_min,:,:,:]                
                elif (index_diff != 1): # more than one data point found 
                    if   (n_dims == 1): 
                        var_5min[n]       = np.nanmean(var_raw[index_min:index_max]) 
                    elif (n_dims == 2): 
                        #var_5min[n,:]     = np.nanmean(var_raw[index_min:index_max,:]) 
                        for n2 in range(0, n_dim2, 1):   
                            var_5min[n,n2] = np.nanmean(var_raw[index_min:index_max,n2]) 
                    elif (n_dims == 3): 
                        #var_5min[n,:,:]   = np.nanmean(var_raw[index_min:index_max,:,:]) 
                        for n2 in range(0, n_dim2, 1):   
                            for n3 in range(0, n_dim3, 1):   
                                  var_5min[n,n2,n3] = np.nanmean(var_raw[index_min:index_max,n2,n3]) 
                    elif (n_dims == 4): 
                        #var_5min[n,:,:,:] = np.nanmean(var_raw[index_min:index_max,:,:,:]) 
                        for n2 in range(0, n_dim2, 1):   
                            for n3 in range(0, n_dim3, 1):   
                                for n4 in range(0, n_dim4, 1):   
                                  var_5min[n,n2,n3,n4] = np.nanmean(var_raw[index_min:index_max,n2,n3,n4]) 
                del index_diff       
        # note csmith 2016/04/26 - add these two lines of code below for most recent data point 
        elif (index_min == nt-1 and index_max == 0): # right most data point 
            if   (n_dims == 1): 
                var_5min[n]       = np.nanmean(var_raw[index_min]) 
            elif (n_dims == 2): 
                #var_5min[n,:]     = np.nanmean(var_raw[index_min,:]) 
                for n2 in range(0, n_dim2, 1):   
                    var_5min[n,n2] = np.nanmean(var_raw[index_min,n2]) 
            elif (n_dims == 3): 
                #var_5min[n,:,:]   = np.nanmean(var_raw[index_min,:,:]) 
                for n2 in range(0, n_dim2, 1):   
                    for n3 in range(0, n_dim3, 1):   
                        var_5min[n,n2,n3] = np.nanmean(var_raw[index_min,n2,n3]) 
            elif (n_dims == 4): 
                #var_5min[n,:,:,:] = np.nanmean(var_raw[index_min,:,:,:]) 
                for n2 in range(0, n_dim2, 1):   
                    for n3 in range(0, n_dim3, 1):   
                        for n4 in range(0, n_dim4, 1):   
                          var_5min[n,n2,n3,n4] = np.nanmean(var_raw[index_min,n2,n3,n4])
        del index_min, index_max  

    return var_5min  

###############################################################################
def read_sfc_obs_csv_data(file_name_full_path, replace_nan_with_null): 
    
    np.warnings.filterwarnings('ignore')    
    #import warnings
    #warnings.simplefilter('ignore', RuntimeWarning) # nanmean of all nan
    
    stn_read_df = pd.read_csv(file_name_full_path,index_col=0)
    #temp_read  = np.array(stn_read_df['temp'])
    #ws_read    = np.array(stn_read_df['ws'])
    #wsg_read   = np.array(stn_read_df['wsg'])
    #wd_read    = np.array(stn_read_df['wd'])
    #rh_read    = np.array(stn_read_df['rh'])
    #alt_read   = np.array(stn_read_df['alt'])
    #slp_read   = np.array(stn_read_df['slp'])

    # datetime_obs_temp = stn_read_df.index # object 
    # nt_obs = len(datetime_obs_temp)
    # datetime_str = ["%s" % x for x in datetime_obs_temp] 
    # datetime_obs_read_utc = np.full([nt_obs], np.nan, dtype=object)
    # for n in range(0, nt_obs, 1):
    #     try: 
    #         datetime_obs_read_utc[n] = datetime.datetime.strptime(datetime_str[n],'%Y-%m-%d %H:%M:00')
    #     except: 
    #         try:
    #             datetime_obs_read_utc[n] = datetime.datetime.strptime(datetime_str[n],'%Y-%m-%d')
    #         except:
    #             datetime_obs_read_utc[n] = datetime.datetime.strptime(datetime_str[n],'%m/%d/%Y %H:%M')
                
    #datetime_obs_read_utc = []
    #for n in range(0, nt_obs, 1):
    #    datetime_obs_read_utc.append(datetime.datetime.strptime(datetime_str[n],'%Y-%m-%d %H:%M:00') - datetime.timedelta(hours=utc_conversion)) # UTC to LST 

    #del stn_read_df_matrix 
    #del datetime_str, nt_obs 

    #stn_data = [temp_read, ws_read, wd_read, rh_read, alt_read, slp_read, swrad_read]
    #stn_data = np.transpose(stn_data) 
    #stn_read_df = pd.DataFrame(stn_data, index=datetime_obs_read_utc, columns=['temp','ws','wd', 'rh', 'alt', 'slp', 'swrad']) 
    #stn_data = [temp_read, ws_read, wsg_read, wd_read, rh_read, alt_read, slp_read, swrad_read]
    #stn_data = np.transpose(stn_data) 
    #stn_read_df = pd.DataFrame(stn_data, index=datetime_obs_read_utc, columns=['temp','ws','wsg','wd', 'rh', 'alt', 'slp', 'swrad']) 

    # replace nan will NULL, required for postgres, this should my to function 
    #if (replace_nan_with_null):
    #    var_temp = temp_read
    #    index_nan = ([np.isnan(var_temp)]) 
    #    var_temp = var_temp.astype(object)
    #    var_temp[index_nan] = 'NULL'
    #    temp_read = var_temp
    #    del index_nan 
            
    return stn_read_df
   
    
###############################################################################
def obs_historical_process(dict_stn_metadata, utc_conversion, time_zone_label, stn_id_pair_list_to_plot, bucket_name):

    # debug KWMC-KSAC 2018/11/07 - 2018/11/21 
    
    print      ('obs_historical_process begin ')
    logger.info('obs_historical_process begin ')

    dir_sfc_obs_historical = os.path.join('data', 'sfc_obs_historical')
    utc_conversion = 8
    dt_start = dt(2000, 1, 1)
    dt_end   = dt(2020, 1, 1)
    #dt_start = dt(2018, 11, 6)
    #dt_end   = dt(2018, 11, 21)
    #dt_start = dt(2018, 10, 10)
    #dt_start = dt(2018, 10,  1)
    #dt_start = dt(2019,  9, 1)
    #dt_start = dt(2017,  9,  1)
    #dt_end   = dt(2019, 11, 15)
    #dt_end = dt.utcnow()

    n_days = (dt_end - dt_start).days 

    # hourly
    #obs_window_minutes = 29 
    #n_hrs = n_days*24
    #dt_axis_hr_lst = []
    #for n in range(0, n_hrs): 
    #    dt_axis_hr_lst.append(dt_start + td(hours=n))
    #print      ('dt_axis_hr_lst is %s - %s ' % (dt_axis_hr_lst[0].strftime('%Y-%m-%d %H:%M'), dt_axis_hr_lst[-1].strftime('%Y-%m-%d %H:%M'))) 
    #logger.info('dt_axis_hr_lst is %s - %s ' % (dt_axis_hr_lst[0].strftime('%Y-%m-%d %H:%M'), dt_axis_hr_lst[-1].strftime('%Y-%m-%d %H:%M')))     
    #dummy_axis = np.arange(0, n_hrs)
    #axis_hr_lst_df = pd.DataFrame(dummy_axis, index=dt_axis_hr_lst)

    # 5 min
    obs_window_minutes = 2 
    n_5min = n_days*24*12
    #dt_axis_hr_utc = []
    dt_axis_5min_lst = []
    for n in range(0, n_5min): 
        dt_axis_5min_lst.append(dt_start + td(minutes=5*n))   
    print      ('dt_axis_5min_lst is %s - %s ' % (dt_axis_5min_lst[0].strftime('%Y-%m-%d %H:%M'), dt_axis_5min_lst[-1].strftime('%Y-%m-%d %H:%M'))) 
    logger.info('dt_axis_5min_lst is %s - %s ' % (dt_axis_5min_lst[0].strftime('%Y-%m-%d %H:%M'), dt_axis_5min_lst[-1].strftime('%Y-%m-%d %H:%M')))     
    dummy_axis = np.arange(0, n_5min)
    axis_5min_lst_df = pd.DataFrame(dummy_axis, index=dt_axis_5min_lst)
    
    slp_obs_5min_s  = np.full([n_5min, dict_stn_metadata['n_stn']], np.nan, dtype='float') 
    #alt_obs_5min_s  = np.full([n_5min, dict_stn_metadata['n_stn']], np.nan, dtype='float') 
    
    replace_nan_with_null = False
    
    s = 2 # KSAC
    s = 9 # KWMC
    # for s in range(0, dict_stn_metadata['n_stn']):
    for s in [1, 4, 9, 10]:
         
        # done s - 1,4
         
        if (dict_stn_metadata['stn_id'][s] in stn_list_to_use):
            #if (s == 2 or s == 9):
            print      ('  processing s %s, s = %s of %s ' % (dict_stn_metadata['stn_id'][s], s, dict_stn_metadata['n_stn']))  
            logger.info('  processing s %s, s = %s of %s ' % (dict_stn_metadata['stn_id'][s], s, dict_stn_metadata['n_stn']))  
            file_name_list = glob.glob(os.path.join(dir_sfc_obs_historical,'stn_obs*'+dict_stn_metadata['stn_id'][s]+'*csv')) 
            file_name_list.sort()
            n_files = len(file_name_list)
            print      ('  stn_id %s, n_files %s ' % (dict_stn_metadata['stn_id'][s], n_files)) 
            logger.info('  stn_id %s, n_files %s ' % (dict_stn_metadata['stn_id'][s], n_files)) 
            f_count = 0
            if (n_files > 0): 
                for f in range(0, n_files, 1): 
                    file_name_full_path = file_name_list[f] 
                    #if ('2014' in file_name_full_path or '2015' in file_name_full_path):
                    #if ('2016' in file_name_full_path):
                    #if ('20' in file_name_full_path):
                    print      ('    file %s of %s ' % (f, n_files))
        
                    stn_read_df = read_sfc_obs_csv_data(file_name_full_path, replace_nan_with_null)
                    # convert dt string to dt type and convert to lst     
                    dt_read_lst  = pd.to_datetime(stn_read_df.index) - td(hours=8)
                    stn_read_df = stn_read_df.set_index(dt_read_lst)
                    #stn_read_df.index    
                    if (f_count == 0):
                        stn_read_df_f = stn_read_df
                    else: 
                        stn_read_df_f = pd.concat([stn_read_df_f, stn_read_df])
                    del stn_read_df
                    f_count += 1
    
                print      ('    datematch start ' ) 
                logger.info('    datematch start ' ) 
                #var_raw = np.vstack((stn_read_df_f['pres'].values, stn_read_df_f['alt'].values, stn_read_df_f['slp'].values)).T
                
                #print(len(stn_read_df_f), n_5min)
                # var_raw = np.vstack((stn_read_df_f['alt'].values, stn_read_df_f['slp'].values)).T
     
                var_5min = datematch_to_5min(stn_read_df_f['slp'].values, stn_read_df_f.index, dt_axis_5min_lst, obs_window_minutes)
                slp_obs_5min_s [:,s] = var_5min
                del var_5min, stn_read_df_f 

    print      ('  read stn data end ' ) 
    logger.info('  read stn data end ' ) 
    
    n_stn_pair = len(stn_id_pair_list_to_plot)
    #pres_diff_5min_s = np.full([n_5min, n_stn_pair], np.nan, dtype=float)
    #alt_diff_5min_s  = np.full([n_5min, n_stn_pair], np.nan, dtype=float)
    slp_diff_5min_s  = np.full([n_5min,n_stn_pair], np.nan, dtype=float)
    print      ('  calculating pressure difference station pairs')
    logger.info('  calculating pressure difference station pairs')
    stn_id_pair = stn_id_pair_list_to_plot[0]
    for s, stn_id_pair in enumerate(stn_id_pair_list_to_plot):
        stn_id1, stn_id2 = stn_id_pair.split('-')[0], stn_id_pair.split('-')[1]
        s_id1 = list(dict_stn_metadata['stn_id']).index(stn_id1)
        s_id2 = list(dict_stn_metadata['stn_id']).index(stn_id2)
        #dict_stn_metadata['stn_id'][s_id1]
        #dict_stn_metadata['stn_id'][s_id2]
        #pres_diff_5min_s[:,s1*dict_stn_metadata['n_stn']+s2] = pres_obs_5min_s[:,s1] - pres_obs_5min_s[:,s2] 
        #alt_diff_5min_s [:,s] = alt_obs_5min_s[:,s_id1] -  alt_obs_5min_s[:,s_id2] 
        slp_diff_5min_s [:,s] = slp_obs_5min_s[:,s_id1] -  slp_obs_5min_s[:,s_id2] 
        #slp_diff_5min_s [:,s1*dict_stn_metadata['n_stn']+s2] =  slp_obs_5min_s[:,s1] -  slp_obs_5min_s[:,s2] 
        #stn_id_pair_list[s1*dict_stn_metadata['n_stn']+s2] = dict_stn_metadata['stn_id'][s1]+'-'+dict_stn_metadata['stn_id'][s2]
    # del slp_obs_5min_s
    # del pres_obs_5min_s, alt_obs_5min_s
            
    print      ('  create slp_diff df ') 
    logger.info('  create slp_diff df ') 
    # create df of the arrays        
    #pres_diff_5min_s_df = pd.DataFrame(pres_diff_5min_s, index=dt_axis_5min_lst, columns=stn_id_pair_list_to_plot).round(2)
    #del pres_diff_5min_s
    #alt_diff_5min_s_df  = pd.DataFrame( alt_diff_5min_s, index=dt_axis_5min_lst, columns=stn_id_pair_list_to_plot).round(2)
    #del alt_diff_5min_s
    slp_diff_5min_s_df  = pd.DataFrame( slp_diff_5min_s, index=dt_axis_5min_lst, columns=stn_id_pair_list_to_plot).round(2)

    #for n in range(0, n_5min):
    #for n in range(1420, 1760):
    #    print(' %s, %s, %s, %s ' % ( dt_axis_5min_lst[n].strftime('%Y-%m-%d %H:%M'), alt_diff_5min_s_df['KWMC-KSAC'][n], alt_obs_5min_s[n,9], alt_obs_5min_s[n, 2])) 
    #del alt_diff_5min_s
 
    # roll up to daily daily max
    print      ('  calculating daily roll-ups') 
    logger.info('  calculating daily roll-ups') 
    
    #pres_diff_day_s_df = pres_diff_5min_s_df.resample('D').max()
    slp_diff_day_s_df = slp_diff_5min_s_df.resample('D').max()
    #alt_diff_day_s_df =  alt_diff_5min_s_df.resample('D').max()
    #pres_diff_day_s_df['KWMC-KSAC'].head()
    #alt_diff_day_s_df['KWMC-KSAC'].head()
    #slp_diff_day_s_df['KWMC-KSAC'].head(50)
        
    print      ('  find top events ') 
    logger.info('  find top events ') 
    
    
    
    # find top events and write to file
    #n_top_events = 20
    n_top_events = 20
    #stn_id_pair = 'KWMC-KSFO'
    #stn_id_pair = 'KDAG-KLAX'
    #s = stn_id_pair_list_to_plot.index('KWMC-KSAC')
    s = stn_id_pair_list_to_plot.index(stn_id_pair)
    for s,stn_id_pair in enumerate(stn_id_pair_list_to_plot):
        #if stn_id_pair == 'KWMC-KSAC':
        #if stn_id_pair in stn_id_pair_list_to_plot:
        slp_top_events_df  =  slp_diff_day_s_df[stn_id_pair].nlargest(n_top_events).round(1)
        #alt_top_events_df  =  alt_diff_day_s_df[stn_id_pair].nlargest(n_top_events).round(1)
        if len(slp_top_events_df) > 0:
            #slp_top_events_df = pres_diff_day_s_df[stn_id_pair].nlargest(n_top_events).round(1)
            #file_name_stn_write = os.path.join('top_events', 'slp_diff_'+stn_id_pair+'.csv') 
            #slp_top_events_df.to_csv(file_name_stn_write) 
            # write file to csv 
            #alt_top_events_df = alt_diff_day_s_df[stn_id_pair].nlargest(n_top_events).round(1)
            #file_name_stn_write = os.path.join('top_events', 'alt_diff_'+stn_id_pair+'.csv') 
            #alt_top_events_df.to_csv(file_name_stn_write) 
            #file_name_stn_write = os.path.join('top_events', 'pres_diff_'+stn_id_pair+'.csv') 
            #pres_top_events_df.to_csv(file_name_stn_write) 
            print      ('%s top events ' %(stn_id_pair)) 
            logger.info('%s top events ' %(stn_id_pair)) 
            i = 8
            #for i, row in enumerate(slp_top_events_df):
            print      ('  slp')
            logger.info('  slp')
            for i in range(0, n_top_events):
                print      ('     %s,  %s  %s ' %(str(i+1).zfill(2), slp_top_events_df.index[i].strftime('%Y-%m-%d'), slp_top_events_df[i]))
                logger.info('     %s,  %s  %s ' %(str(i+1).zfill(2), slp_top_events_df.index[i].strftime('%Y-%m-%d'), slp_top_events_df[i]))
            #print      ('  alt')
            #logger.info('  alt')
            #for i in range(0, n_top_events):
            #    print      ('     %s,  %s  %s ' %(str(i+1).zfill(2), alt_top_events_df.index[i].strftime('%Y-%m-%d'), alt_top_events_df[i]))
            #    logger.info('     %s,  %s  %s ' %(str(i+1).zfill(2), alt_top_events_df.index[i].strftime('%Y-%m-%d'), alt_top_events_df[i]))
            #print      ('  pres')
            #logger.info('  pres')
            #for i in range(0, n_top_events):
            #    print      ('     %s,  %s  %s ' %(str(i+1).zfill(2), pres_top_events_df.index[i].strftime('%Y-%m-%d'), pres_top_events_df[i]))
            #    logger.info('     %s,  %s  %s ' %(str(i+1).zfill(2), pres_top_events_df.index[i].strftime('%Y-%m-%d'), pres_top_events_df[i]))

            ################################################
            # plot cdf 
            mask = ~np.isnan(alt_diff_day_s_df[stn_id_pair])
            var_temp = alt_diff_day_s_df[stn_id_pair][mask]
            #np.min(var_temp)
            #np.max(var_temp)
            [x_min, x_max, x_int] = [float(math.floor(np.min(var_temp))), float(math.ceil(np.max(var_temp))), 2.0]
            hist, var_bins = np.histogram(var_temp, bins=100, range=[x_min, x_max])
            cdf = 100.0*np.cumsum(hist)/len(var_temp)
            [y_min, y_max, y_int] = [80, 100, 2]
            
            
            index = (cdf < 80.0).argmin()
            [x_min, x_max, x_int] = [float(math.floor(var_bins[index])), float(math.ceil(np.max(var_temp))), 1.0]
            y_ticks = list(np.arange(y_min, y_max+y_int, y_int))
            x_ticks = list(np.arange(x_min, x_max+x_int, x_int))
            # n_days_plot = (dt_max_plot - dt_min_plot).days 
            
            figsize_x, figsize_y = 9, 8
            size_font = 14
            
            fig_num = 141
            fig = plt.figure(num=fig_num,figsize=(figsize_x, figsize_y)) 
            plt.clf()
            plt.plot(var_bins[1:], cdf, 'r', linestyle='-', label=model_name.upper(), linewidth=3.0, marker='o', markersize=0, markeredgecolor='k') 
            #plt.plot(dt_axis_lt_init[i,mask], p_sfc2_diff_init_m_hr_s[i,m,mask,s], color_list[m], linestyle='-', label=model_name, linewidth=3.0, marker='o', markersize=0, markeredgecolor='k') 
            #plt.plot(dt_axis_lt_init[i,:], p_sfc1_diff_init_m_hr_s[i,m,:,s], 'r', linestyle='-', label='obs ws', linewidth=2.0, marker='o', markersize=2, markeredgecolor='k') 
            #plt.legend(loc=3,fontsize=size_font-2,ncol=1) 
            for y_tick in y_ticks:
                plt.plot([x_min, x_max], [y_tick, y_tick], 'gray', linestyle='-', linewidth=0.5, marker='o', markersize=0) 
            for x_tick in x_ticks:
                plt.plot([x_tick, x_tick], [y_min, y_max], 'gray', linestyle='-', linewidth=0.5, marker='o', markersize=0) 
            
            #plt.gca().xaxis.set_major_formatter(DateFormatter(dt_format))
            plt.xticks(x_ticks, visible=True, fontsize=size_font) 
            plt.xlim([x_ticks[0], x_ticks[-1]])
            plt.yticks(y_ticks, fontsize=size_font)
            plt.ylim([y_min, y_max])
            plt.ylabel('CDF [%]',fontsize=size_font,labelpad=00)
            plt.xlabel('$\Delta$ alt [mb]',fontsize=size_font,labelpad=20)
            plt.title('$\Delta$ alt %s, Observed CDF %s - %s ' % (stn_id_pair, dt_start.strftime('%Y-%m-%d'), dt_end.strftime('%Y-%m-%d')), \
              fontsize=size_font+2, x=0.5, y=1.01)                    
            plt.show() 
            #filename = 'del_alt_all_model_'+stn_id_pair+'_'+dt_init_list[i].strftime('%Y-%m-%d_%H')+'_'+str(n_days)+'.png' 
            filename = 'del_alt_cdf_'+stn_id_pair+'.png' 
            plot_name = os.path.join('top_events', filename)
            plt.savefig(plot_name) 
            
            width_line = 2.0
            [x_line1, x_line2, x_line3] = [0.5, 1.5, 2.5]  # 1.0, 2.0, 3.0
             
            line_spacing = 1.0  
            y_line_offset = 0.5 # was 0.2
            n_lines = 20 
            y_top = 21.0 # was 11.0
            
            fig_num = 151 
            fig = plt.figure(num=fig_num,figsize=(8,7)) # was 11,9
            plt.clf() 
            
            for l in range(0, n_lines+1, 1): 
                #print (l)
                #print (l*line_spacing)
                plt.plot([ 0, x_line3], [l*line_spacing, l*line_spacing], 'k', linestyle='-', linewidth=width_line, marker='o', markersize=0) 
            plt.plot([             0,              0], [ 0, y_top], 'k', linestyle='-', linewidth=width_line, marker='o', markersize=0) 
            plt.plot([x_line1, x_line1], [ 0, y_top], 'k', linestyle='-', linewidth=width_line, marker='o', markersize=0) 
            plt.plot([x_line2, x_line2], [ 0, y_top], 'k', linestyle='-', linewidth=width_line, marker='o', markersize=0) 
            plt.plot([x_line3, x_line3], [ 0, y_top], 'k', linestyle='-', linewidth=width_line, marker='o', markersize=0) 
            
            plt.axis('off')
            
            [x_offset, y_offset] = [0.2, 0.5]
            for l in range(0, n_lines, 1): 
                plt.text(               x_offset, l*line_spacing+y_offset, str(n_lines-l).zfill(2), fontsize=size_font,                            ha='left', va='center', color='k')  
                plt.text(x_line1+x_offset, l*line_spacing+y_offset, alt_top_events_df.index[n_lines-l-1].strftime('%Y-%m-%d'), fontsize=size_font, ha='left', va='center', color='k')  
                plt.text(x_line2+x_offset, l*line_spacing+y_offset, alt_top_events_df[n_lines-l-1], fontsize=size_font,                            ha='left', va='center', color='k')  
            # headers
            plt.text(               x_offset, 20.0+y_offset, 'rank', fontsize=size_font,                               ha='left', va='center', color='k')  
            plt.text(x_line1+x_offset, 20.0+y_offset, 'date', fontsize=size_font,                               ha='left', va='center', color='k')  
            plt.text(x_line2+x_offset, 20.0+y_offset, '$\Delta$ alt [mb]', fontsize=size_font,                               ha='left', va='center', color='k')  
            plt.title('$\Delta$ alt %s, Top events %s - %s ' % (stn_id_pair, dt_start.strftime('%Y-%m-%d'), dt_end.strftime('%Y-%m-%d')), \
              fontsize=size_font+2, x=0.5, y=1.01) 
            #plt.xlim([-0.2, 11.2])
            #plt.ylim([-4.2, 12.0]) 
            plt.show() 
            plt.tight_layout()
            filename = 'del_alt_top_events_'+stn_id_pair+'.png' 
            plot_name = os.path.join('top_events', filename)
            plt.savefig(plot_name) 

    print      ('obs_historical_process end ')
    logger.info('obs_historical_process end ')




# KWMC-KSAC top events 
#   slp
  
#   01,  2019-10-30  26.1 
#   04,  2019-10-29  24.5 

#   02,  2017-10-09  25.2 
#   05,  2019-10-10  24.4 

#   03,  2018-11-08  25.1 
#   07,  2018-11-09  23.8 

#   08,  2018-11-11  23.4 
#   11,  2018-11-12  22.1 

#   12,  2017-12-10  22.0 
#   20,  2017-12-11  20.8 
#   10,  2017-12-12  22.5 
#   18,  2017-12-13  21.0 
#   06,  2017-12-14  24.1 

#   09,  2017-12-17  22.7 

#   13,  2019-10-24  21.6 

#   14,  2017-12-05  21.5 

#   15,  2018-10-15  21.5 

#   16,  2017-12-06  21.4 
#   17,  2017-12-07  21.1 

#   19,  2018-11-20  20.9 


# top expected events 
# 2011_12_01

# 2017_10_08

# 2018_10_14
# 2018_11_08

# 2019_06_08
# 2019_09_24
# 2019_10_05
# 2019_10_09
# 2019_10_23
# 2019_10_27

#slp_diff_day_s_df['KDAG-KLAX']['2003-10-21':'2003-10-29']    
#slp_diff_day_s_df['KDAG-KLAX']['2007-10-15':'2007-10-31']    

#12z GFS peaked LAX-DAG gradients at -10.2 and LAX-TPH at -15.42z GF
#Cedar Fire October 25, 2003
#Witch Fire October 21, 2007 



# slp1_diff_day_s_df['KWMC-KSAC']['2017-10-06':'2017-10-12']
# slp1_diff_day_s_df['KWMC-KSAC']['2018-11-05':'2018-11-12']

# slp1_diff_day_s_df['KWMC-KSAC']['2019-10-21':'2019-10-31']
    
# temp,ws,wsg,wd,rh,slp,pres,alt           
# psfc  po * exp(-g h M / (To Ro))
# 1000.0* -9.80665*0.02896968/(288.16*8.314462618)
# 1/0.1185 
# ht in km / 8.43 
# 8.3*288/9.8
# 1000.0/243.9
# slp1 -> slp -> yes
# slp2 -> pres -> no
# slp3 -> alt -> no
# slp4 -> formula above 
# slp5 -> -formula above  -> no
 
# KWMC-KSAC top events 
#   slp1
#      01,  2019-10-30  26.1 
#      02,  2019-10-29  24.5 
#      03,  2019-10-10  24.4 
#      04,  2019-10-24  21.6 
#      05,  2019-10-28  19.3 
#      06,  2019-10-09  19.2 
#      07,  2019-10-11  19.1 
#      08,  2019-10-31  19.0 
#      09,  2019-10-27  18.5 
#      10,  2019-11-01  18.3 
#      11,  2019-10-23  17.8 
#      12,  2019-11-02  17.0 
#      13,  2019-10-25  16.8 
#      14,  2019-10-26  15.4 
#      15,  2019-11-07  15.4 
#      16,  2019-11-05  15.4 
#      17,  2019-11-04  15.4 
#      18,  2019-11-08  15.1 
#      19,  2019-11-11  15.1 
#      20,  2019-10-06  15.0 





###############################################################################
def cleanup(bucket_name):

    print      ('cleanup begin ')
    logger.info('cleanup begin ')

    print      ('  cleanup data directories ')
    logger.info('  cleanup data directories ')


    dt_now = dt.utcnow()
    dir_init_temp = dt_init.strftime('%Y-%m-%d')
    dir_list_ingest    = glob.glob(os.path.join('data', 'ingest', '*'))
    dir_list_processed = glob.glob(os.path.join('data', 'processed', '*'))
    dir_temp = dir_list_ingest[0]
    for dir_temp in dir_list_ingest+dir_list_processed:
        dt_temp = dt.strptime(dir_temp.split('/')[2],'%Y-%m-%d')
        days_diff = (dt_now - dt_temp).days
        #print(days_diff)
        if days_diff >= 2:
            temp_command = 'rm -rf '+dir_temp    
            print      ('  removing %s ' %(dir_temp)) 
            logger.info('  removing %s ' %(dir_temp)) 
            os.system(temp_command)

    print      ('  cleanup logs ')
    logger.info('  cleanup logs ')

    n_days_to_retain = 7.0
    time_now = time.time() 
    log_list = glob.glob(os.path.join('logs', 'log_*'))
    log_list.sort(key=os.path.getmtime)
    log_temp = log_list[0]
    for log_temp in log_list:
        time_temp = os.path.getmtime(log_temp)
        time_delta_days = (time_now - time_temp)/(24.*3600.)
        if (time_delta_days > n_days_to_retain): 
            #try: 
            os.remove(log_temp)
            #os.system('rm '+file_temp)
            #except: 
            #    pass 
        del time_temp, time_delta_days
        
    print      ('cleanup end ')
    logger.info('cleanup end ')
    

###############################################################################    
if __name__ == "__main__":

    # debug_mode = True
    debug_mode = False
    if not debug_mode: 
        # parse inputs 
        parser = argparse.ArgumentParser(description='argparse')
        parser.add_argument('--batch_mode',    type=str, help='operational or backfill', required=False, default='operational')
        parser.add_argument('--model_name',    type=str, help='gfs/nam/hrrr', required=False, default='hrrr')
        parser.add_argument('--process_name',  type=str, help='download/process_grib/process_csv/plot', required=True, default='download')    
        parser.add_argument('--bucket_name',   type=str, help='bucket_name', required=True, default='data')
        args = parser.parse_args()
        model_name    = args.model_name
        process_name  = args.process_name 
        batch_mode = args.batch_mode 
        bucket_name   = args.bucket_name    
    else:
        #os.chdir('/home/csmith/pgrad')
        bucket_name = 'data'
        #model_name = 'hrrr'    
        #model_name = 'nam'    
        model_name = 'gfs'    
        batch_mode = 'operational'
        #batch_mode = 'backfill'
        process_name = 'download'
        #process_name = 'process_grib'
        #process_name = 'process_csv'
        #process_name = 'plot_data'
        #process_name = 'obs_dl_operational'
        #process_name = 'obs_historical_download'
        #process_name = 'obs_historical_process'
        #process_name = 'cleanup'
        
    # os.getcwd()
    os.chdir(os.path.join(os.getenv('HOME'), 'pgrad'))
            
    # sanitize inputs
    model_name_list = ['gfs', 'nam', 'hrrr']
    if model_name not in model_name_list:
        print('ERROR model_name %s not supported' %(model_name))
        sys.exit()
    if process_name not in ['cleanup', 'download', 'process_grib', 'process_csv', 'calc_pgrad', 'plot_data', 'obs_historical_download', 'obs_historical_process']:
        print('ERROR model_name %s not supported' %(process_name))
        sys.exit()
    if batch_mode not in ['operational','backfill']:
        print('ERROR batch_mode %s not supported' %(batch_mode))
        sys.exit()

    if   model_name == 'gfs':
        forecast_horizon_hr = 24*10+1
    elif model_name == 'nam':
        forecast_horizon_hr = 60+1 # 60
    elif model_name == 'hrrr':
        forecast_horizon_hr = 36+1
    # harcode for debugging
    #if debug_mode: 
    #    forecast_horizon_hr = 6
        
    update_frequency_hrs = 6
    # define starting time 
    print      ('define_cron_start_time and local daylight savings time ') 
    dt_start_utc = dt.utcnow()
    (utc_conversion, time_zone_label) = define_daylight_savings_or_not(dt_start_utc) 
    dt_start_lt = dt.utcnow() - td(hours=utc_conversion)
    
    # create_log_file
    print      ('create_log_file' ) 
    if  process_name in ['download', 'process_grib', 'process_csv', 'calc_pgrad']:
        log_file_name = 'log_'+process_name+'_'+model_name+'_'+dt_start_lt.strftime('%Y-%m-%d_%H-%M')+'.txt' 
    else:
        log_file_name = 'log_'+process_name+'_'+dt_start_lt.strftime('%Y-%m-%d_%H-%M')+'.txt' 
    log_name_full_file_path = os.path.join('logs', log_file_name) 
    logger = create_log_file(log_name_full_file_path, dt_start_utc, time_zone_label) 

    # get next expected forecast to be available 
    dt_init_expected = define_expected_forecast_available_from_wallclock(logger, model_name, update_frequency_hrs)
    
    if   batch_mode == 'operational':
        hours_to_backfill = 0
    elif batch_mode == 'backfill':
        hours_to_backfill = 24

    # read station data 
    use_stn = 'all'
    print_stn_info = False
    #read_stn_metadata_type = 'csv' # 'db' or 'csv'
    project_name = 'pgrad'
    stn_metadata_file_name = os.path.join(os.environ['HOME'], project_name, 'station_list_'+project_name+'.csv') 
    (dict_stn_metadata) = read_stn_metadata_from_csv(stn_metadata_file_name, use_stn, print_stn_info)

    #stn_id_pair_list_to_plot = [
    #    'KDAG-KLAX',
    #    'KWMC-KSFO']

    # stn_id_pair_list_to_plot = [
    #     'KMFR-KSAC',
    #     'KMFR-KSFO',
    #     'KRDD-KSAC',
    #     'KRDD-KBFL',
    #     'KRDD-KSFO',
    #     'KWMC-KSAC',
    #     'KWMC-KSFO']

    stn_id_pair_list_to_plot = [
        'KACV-KSFO',
        'KBFL-KSBA',
        'KDAG-KLAX',
        'KMFR-KRDD',
        'KMFR-KSAC',
        'KMFR-KSFO',
        'KRDD-KSAC',
        'KSFO-KSAC',
        'KSMX-KSBA',
        'KWMC-KSAC',
        'KWMC-KSFO']

    # top stns - 4
    #KSFO
    #KWMC 
    #KDAG
    #KLAX
    
    # second stns 10 (4+6) 
    #KSAC
    #KMFR
    #KRDD
    #KBFL
    #KSBA 
    #KSMX 
        
    stn_list_to_use = set()
    for pair in stn_id_pair_list_to_plot:
        stn1, stn2 = pair.split('-')[0], pair.split('-')[1]
        stn_list_to_use.add(stn1)
        stn_list_to_use.add(stn2)
    stn_list_to_use = list(stn_list_to_use)
    # print(stn_list_to_use)
    # stn_list_to_use = ['KBFL', 'KSMX', 'KSBA', 'KLAX', 'KDAG', 'KSFO', 'KACV', 'KWMC', 'KSAC', 'KMFR', 'KRDD']
     
    dt_init = dt_init_expected - td(hours=hours_to_backfill)
    if  process_name in ['download', 'process_grib', 'process_csv', 'calc_pgrad']:
        while dt_init <= dt_init_expected: 
            print      ('***************************')
            logger.info('***************************')
            print      ('processing init %s ' % (dt_init.strftime('%Y-%m-%d_%H-%M')))
            logger.info('processing init %s ' % (dt_init.strftime('%Y-%m-%d_%H-%M')))
            print('executing process %s' %(process_name))
            if   process_name == 'download':
                download_data(model_name, dt_init, forecast_horizon_hr, bucket_name)
            elif process_name == 'process_grib':
                process_grib_data(dict_stn_metadata, model_name, dt_init, forecast_horizon_hr, bucket_name)
            elif process_name == 'process_csv':
                process_csv_data(dict_stn_metadata, model_name, dt_init, forecast_horizon_hr, bucket_name)
            elif process_name == 'calc_pgrad':                
                calc_pgrad(dict_stn_metadata, stn_id_pair_list_to_plot, model_name, dt_init, bucket_name)
                #calc_pgrad(dict_stn_metadata, model_name_list, dt_init, bucket_name)
            dt_init += td(hours=update_frequency_hrs)

    dt_init = dt_init_expected
    if process_name == 'plot_data':
        #plot_data(model_name_list, dt_init, forecast_horizon_hr=120+1, bucket_name)
        plot_data(dict_stn_metadata, model_name_list, dt_init, 241, dt_start_lt, utc_conversion, time_zone_label, stn_id_pair_list_to_plot, bucket_name)
    if process_name == 'obs_historical_download':
        obs_historical_download(dict_stn_metadata, stn_list_to_use, utc_conversion, time_zone_label, bucket_name)
    if process_name == 'obs_historical_process':
        obs_historical_process(dict_stn_metadata, utc_conversion, time_zone_label, stn_id_pair_list_to_plot, bucket_name)
    if process_name == 'cleanup':
        cleanup(bucket_name)
  
    # close log file
    print      ('close_logger begin ')
    logger.info('close_logger begin ')
    close_logger(logger, process_name, dt_start_lt, utc_conversion, time_zone_label) 

###############################################################################    




