
'''
name: pgrad.py 
purpose: process and analyze pressure gradient forcing from NWP models 
author: Craig Smith, craig.matthew.smith@gmail.com
usage: ./src/run.sh n  where n is the number of batteries to analyze [1-5]
repo: https://github.com/weathertrader/battery_charge
'''

# python ./src/pgrad.py --model_name=hrrr --process_name=download --bucket_name=data --batch_mode=operational
# python ./src/pgrad.py --model_name=hrrr --process_name=process_grib --bucket_name=data --batch_mode=operational
# python ./src/pgrad.py --model_name=hrrr --process_name=process_csv --bucket_name=data --batch_mode=operational

# python ./src/pgrad.py --model_name=nam --process_name=download --bucket_name=data --batch_mode=operational
# python ./src/pgrad.py --model_name=nam --process_name=process_grib --bucket_name=data --batch_mode=operational
# python ./src/pgrad.py --model_name=nam --process_name=process_csv --bucket_name=data --batch_mode=operational

# python ./src/pgrad.py --model_name=gfs --process_name=download --bucket_name=data --batch_mode=operational
# python ./src/pgrad.py --model_name=gfs --process_name=process_grib --bucket_name=data --batch_mode=operational
# python ./src/pgrad.py --model_name=gfs --process_name=process_csv --bucket_name=data --batch_mode=operational

# python ./src/pgrad.py --process_name=calc_pgrad --bucket_name=data --batch_mode=operational


######################################
# mvp pgrad - 10 full days

# 1d   static png plots
#      latest init, all models
#      single model, last 4 inits
#      3d, 5d, 10d 
#      station pairs 

# 2d   website static jquery

# 2d   deploy to ec2 or gcp 

# 1d   website from local to www

# 2d   station observations historical
#      download
#      roll-up to daily
#      tables of top historical events 

# 2d   stn obs operational  
#      download local
#      download static

# 1/2d update forecasts avail csv 

# 1d   units conversion
#      calc p_sfc from which variable

######################################
# after deployment of mvp 
# code -> lambda, operationalize - 1d  
#     front end dynamic 
# url deploy, infra, recovery - 2d 
# 1 d local -> s3
#     download 
#     process 
#     log 
#     plots
# 1/2d redo stn list
# 1/2d redo all historical obs dl and process
# 1/2d environment, requirements.txt, clean up repo add readme 




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
    time_delta_minutes = (dt_start_lt - dt_end_lt).seconds/3600.0
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
                return
            else:             
                print      ('    file exists on remote')
                logger.info('    file exists on remote')
  
                if   (model_name == 'hrrr'):
                    # curl_command = 'curl "https://nomads.ncep.noaa.gov/cgi-bin/filter_hrrr_2d.pl?file='+file_name_remote+'&lev_10_m_above_ground=on&lev_2_m_above_ground=on&lev_surface=on&var_HGT=on&var_PRES=on&var_RH=on&var_TMP=on&var_UGRD=on&var_VGRD=on&var_APCP=on&var_DPT=on&var_FRICV=on&var_GUST=on&var_LAND=on&var_WIND=on&var_HGT=on&var_PRES=on&var_RH=on&var_TMP=on&var_UGRD=on&var_VGRD=on&subregion=&leftlon=-160&rightlon=-110&toplat=50&bottomlat=25&dir=%2Fhrrr.'+url_folder_str+'%2Fconus" -o '+file_name_ingest
                    # curl_command = 'curl "https://nomads.ncep.noaa.gov/cgi-bin/filter_hrrr_2d.pl?file='+file_name_remote+'&lev_2_m_above_ground=on&lev_mean_sea_level=on&lev_surface=on&var_HGT=on&var_MSLMA=on&var_PRES=on&var_APCP=on&var_UGRD=on&var_VGRD=on&subregion=&leftlon=-160&rightlon=-110&toplat=50&bottomlat=25&dir=%2Fhrrr.'+url_folder_str+'%2Fconus" -o '+file_name_ingest
                    # curl_command = 'curl "https://nomads.ncep.noaa.gov/cgi-bin/filter_hrrr_2d.pl?file='+file_name_remote+'&lev_mean_sea_level=on&lev_surface=on&var_HGT=on&var_MSLMA=on&var_PRES=on&var_UGRD=on&var_VGRD=on&subregion=&leftlon=-160&rightlon=-110&toplat=50&bottomlat=25&dir=%2Fhrrr.'+url_folder_str+'%2Fconus" -o '+file_name_ingest
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
                    # gfs 
                    # works
                    # curl_command = 'curl "https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl?file=gfs.t12z.pgrb2.0p25.f000&lev_mean_sea_level=on&lev_surface=on&var_PRES=on&var_PRMSL=on&subregion=&leftlon=-160&rightlon=-110&toplat=50&bottomlat=25&dir=%2Fgfs.20200810%2F12" -o '+file_name_ingest
                    # curl_command = 'curl "https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl?file=gfs.t12z.pgrb2.0p25.f000&lev_mean_sea_level=on&lev_surface=on&var_PRES=on&var_PRMSL=on&subregion=&leftlon=-160&rightlon=-110&toplat=50&bottomlat=25&dir=%2F'+url_folder_str1+'%2F12" -o '+file_name_ingest
                    # use this one 
                    curl_command = 'curl "https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl?file=gfs.t'+dt_init.strftime('%H')+'z.pgrb2.0p25.f'+str(hr).zfill(3)+'&lev_mean_sea_level=on&lev_surface=on&var_PRES=on&var_PRMSL=on&subregion=&leftlon=-160&rightlon=-110&toplat=50&bottomlat=25&dir=%2F'+url_folder_str1+'%2F12" -o '+file_name_ingest
                    # https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25_1hr.pl?file=gfs.t12z.pgrb2.0p25.anl&lev_mean_sea_level=on&lev_surface=on&var_PRES=on&var_PRMSL=on&leftlon=0&rightlon=360&toplat=90&bottomlat=-90&dir=%2Fgfs.20200811%2F12
                    # https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl?file=gfs.t12z.pgrb2.0p25.anl&lev_mean_sea_level=on&lev_surface=on&var_PRES=on&var_PRMSL=on&leftlon=0&rightlon=360&toplat=90&bottomlat=-90&dir=%2Fgfs.20200811%2F12
                 
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
def process_grib_data(model_name, dt_init, forecast_horizon_hr, bucket_name):

    print      ('process_grib_data begin ')
    logger.info('process_grib_data begin ')
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
    file_list = glob.glob(os.path.join(dir_name_ingest, model_name+'*.grib2'))
    n_files = len(file_list)
    print      ('found %s files to process' %(n_files))
    logger.info('found %s files to process' %(n_files))
    if n_files == 0:
        print      ('no files to process')
        logger.info('no files to process')
        return
        # sys.exit() 
        
    initial_read = False

    file_temp = file_list[0]
    for n, file_temp in enumerate(file_list): 
        
        print      ('  processing file %s of %s' %(n, n_files))
        logger.info('  processing file %s of %s' %(n, n_files))

        #file_name = os.path.dirname(file_temp)
        file_name = os.path.basename(file_temp)
        file_name_processed = os.path.join(dir_name_processed, file_name)

        ds_read = xr.open_dataset(file_temp, engine='cfgrib')        
        #sorted(ds_read.variables)
        # ds_sfc = xr.open_dataset(file_temp, engine='cfgrib',
        #      backend_kwargs={'filter_by_keys': {'typeOfLevel': 'surface'}})
        # ds_2m = xr.open_dataset(file_temp, engine='cfgrib',
        #       backend_kwargs={'filter_by_keys': {'typeOfLevel': 'heightAboveGround', 'level': 2}})
        # ds_10m = xr.open_dataset(file_temp, engine='cfgrib',
        #      backend_kwargs={'filter_by_keys': {'typeOfLevel': 'heightAboveGround', 'level': 10}})
        
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
            print_flag = True
            (j_loc_s, i_loc_s) = map_stn_locations_to_grid_locations(logger, dict_stn_metadata, lon_2d, lat_2d, print_flag)
            initial_read = True

        #dt_init = ds_read['time']
        dt_valid = ds_read['valid_time']
        
        if model_name == 'hrrr':
            p1_sfc_2d = ds_read['mslma']  
            p2_sfc_2d = ds_read['sp']  
            # mslma 
        elif model_name == 'nam':
            p1_sfc_2d = ds_read['prmsl']
            p2_sfc_2d = np.array(ds_read['sp'])
        elif model_name == 'gfs':
            p1_sfc_2d = ds_read['prmsl']
            p2_sfc_2d = np.array(ds_read['sp'])
            #p2_sfc_2d = np.array(ds_read['meanSea'])
        
        print('lon_2d min max is %5.2f %5.2f ' %(np.nanmin(lon_2d), np.nanmax(lon_2d)))
        print('lat_2d min max is %5.2f %5.2f ' %(np.nanmin(lat_2d), np.nanmax(lat_2d)))
        
        print('p1_sfc_2d min max is %5.2f %5.2f ' %(np.nanmin(p1_sfc_2d), np.nanmax(p1_sfc_2d)))
        print('p2_sfc_2d min max is %5.2f %5.2f ' %(np.nanmin(p2_sfc_2d), np.nanmax(p2_sfc_2d)))

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
        print      ('    stn_file_name %s ' % (stn_file_name)) 
        logger.info('    stn_file_name %s ' % (stn_file_name)) 

        print      ('write p_sfc begin ')
        logger.info('write p_sfc begin ')
        column_str = ['stn_id', 'p1', 'p2']
        p_sfc_data = [dict_stn_metadata['stn_id'], p1_sfc_stn, p2_sfc_stn]
        #stn_info_transpose = numpy.transpose(stn_info) 
        p_sfc_df = pd.DataFrame(np.transpose(p_sfc_data), columns=column_str) 
        #stn_info_df = stn_info_df.sort_values(by='stn_mnet_id') 
        # stn_info_df = stn_info_df.sort_values(by='stn_name') 
        p_sfc_df.to_csv(stn_file_name) 
        print      ('write p_sfc end ')   
        logger.info('write p_sfc end ')   

        # archive raw grib file 
        temp_command = 'mv -f '+file_temp+' '+file_name_processed
        print      ('    archive output %s ' % (temp_command)) 
        logger.info('    archive output %s ' % (temp_command)) 
        os.system(temp_command)
        print      ('    archive output: success ' ) 
        logger.info('    archive_output: success ' ) 
        
    # clean up idx files
    temp_command = 'rm -f '+dir_name_ingest+'/*.idx'    
    print      ('    clean up idx files ') 
    logger.info('    clean up idx files ') 
    os.system(temp_command)
    print      ('process_grib_data end ')
    logger.info('process_grib_data end ')


###############################################################################
def process_csv_data(model_name, dt_init, forecast_horizon_hr, bucket_name):

    print      ('process_csv begin ')
    logger.info('process_csv begin ')
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
    file_list = glob.glob(os.path.join(dir_name_ingest, model_name+'*.csv'))
    n_files = len(file_list)
    print      ('found %s files to process' %(n_files))
    logger.info('found %s files to process' %(n_files))
    if n_files == 0:
        print      ('no files to process')
        logger.info('no files to process')
        return
        # sys.exit() 

    # read or create master p_sfc file     
    p_sfc1_master_file = os.path.join(dir_name_processed, model_name+'_p_sfc1_'+dt_init.strftime('%Y-%m-%d_%H')+'_t_all.csv')
    p_sfc2_master_file = os.path.join(dir_name_processed, model_name+'_p_sfc2_'+dt_init.strftime('%Y-%m-%d_%H')+'_t_all.csv')
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
        print      ('  processing file %s of %s' %(n, n_files))
        logger.info('  processing file %s of %s' %(n, n_files))
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
    print       ('write p_sfc master begin ')
    logger.info('write p_sfc master begin ')
    p_sfc1_hr_s_df = pd.DataFrame(p_sfc1_hr_s, index=dt_axis, columns=dict_stn_metadata['stn_id']) 
    p_sfc1_hr_s_df.to_csv(p_sfc1_master_file) 
    p_sfc2_hr_s_df = pd.DataFrame(p_sfc2_hr_s, index=dt_axis, columns=dict_stn_metadata['stn_id']) 
    p_sfc2_hr_s_df.to_csv(p_sfc2_master_file) 
    print      ('write p_sfc master end ')   
    logger.info('write p_sfc master end ')   

    print      ('p_sfc1_hr_s min max is %5.2f %5.2f ' %(np.nanmin(p_sfc1_hr_s), np.nanmax(p_sfc1_hr_s)))
    logger.info('p_sfc1_hr_s min max is %5.2f %5.2f ' %(np.nanmin(p_sfc1_hr_s), np.nanmax(p_sfc1_hr_s)))
    print      ('p_sfc2_hr_s min max is %5.2f %5.2f ' %(np.nanmin(p_sfc2_hr_s), np.nanmax(p_sfc2_hr_s)))
    logger.info('p_sfc2_hr_s min max is %5.2f %5.2f ' %(np.nanmin(p_sfc2_hr_s), np.nanmax(p_sfc2_hr_s)))

    # archive csv ingest file to processed
    for file_temp in file_list: 
        #file_name = os.path.dirname(file_temp)
        file_name = os.path.basename(file_temp)
        file_name_processed = os.path.join(dir_name_processed, file_name)
        temp_command = 'mv -f '+file_temp+' '+file_name_processed
        print      ('    archive output %s ' % (temp_command)) 
        logger.info('    archive output %s ' % (temp_command)) 
        os.system(temp_command)
        print      ('    archive output: success ' ) 
        logger.info('    archive_output: success ' ) 
    print      ('process_csv end ')
    logger.info('process_csv end ')


###############################################################################
def calc_pgrad(model_name_list, dt_init, bucket_name):

    print      ('calc_pgrad begin ')
    logger.info('calc_pgrad begin ')

    # read station data 
    use_stn = 'all'
    print_stn_info = 0
    #read_stn_metadata_type = 'csv' # 'db' or 'csv'
    project_name = 'pgrad'
    stn_metadata_file_name = os.path.join(os.environ['HOME'], project_name, 'station_list_'+project_name+'.csv') 
    (dict_stn_metadata) = read_stn_metadata_from_csv(stn_metadata_file_name, use_stn, print_stn_info)

    dir_init_temp = dt_init.strftime('%Y-%m-%d')
    dir_name_ingest    = os.path.join('data', 'ingest',    dir_init_temp)
    dir_name_processed = os.path.join('data', 'processed', dir_init_temp)

    model_name = 'hrrr'
    for model_name in model_name_list:
        print      ('  processing %s ' %(model_name))
        logger.info('  processing %s ' %(model_name))
        # read p_sfc file     
        p_sfc1_master_file = os.path.join(dir_name_processed, model_name+'_p_sfc1_'+dt_init.strftime('%Y-%m-%d_%H')+'_t_all.csv')
        p_sfc2_master_file = os.path.join(dir_name_processed, model_name+'_p_sfc2_'+dt_init.strftime('%Y-%m-%d_%H')+'_t_all.csv')
        p_sfc1_diff_master_file = os.path.join(dir_name_processed, model_name+'_p_sfc1_diff_'+dt_init.strftime('%Y-%m-%d_%H')+'_t_all.csv')
        p_sfc2_diff_master_file = os.path.join(dir_name_processed, model_name+'_p_sfc2_diff_'+dt_init.strftime('%Y-%m-%d_%H')+'_t_all.csv')
        if not os.path.isfile(p_sfc1_master_file): 
            print      ('  ERROR - input file not found %s ' %(p_sfc1_master_file))
            logger.info('  ERROR - input file not found %s ' %(p_sfc1_master_file))
        else:
            # read master
            p_sfc1_hr_s_df = pd.read_csv(p_sfc1_master_file, index_col=0)
            #p_sfc1_hr_s = p_sfc1_hr_s_df.values
            p_sfc2_hr_s_df = pd.read_csv(p_sfc2_master_file, index_col=0)
            #p_sfc2_hr_s = p_sfc2_hr_s_df.values
            dt_axis = p_sfc1_hr_s_df.index.values
            forecast_horizon_hr = len(dt_axis)

            p_sfc1_diff_hr_s = np.full([forecast_horizon_hr, dict_stn_metadata['n_stn']**2], np.nan, dtype=float)
            p_sfc2_diff_hr_s = np.full([forecast_horizon_hr, dict_stn_metadata['n_stn']**2], np.nan, dtype=float)
            column_str = [None]*dict_stn_metadata['n_stn']**2
            s1 = 3
            s2 = 5
            for s1 in range(0, dict_stn_metadata['n_stn']):
                for s2 in range(0, dict_stn_metadata['n_stn']):
                    p_sfc1_diff_hr_s[:,s1*dict_stn_metadata['n_stn']+s2] = p_sfc1_hr_s_df[dict_stn_metadata['stn_id'][s1]] - p_sfc1_hr_s_df[dict_stn_metadata['stn_id'][s2]]
                    p_sfc2_diff_hr_s[:,s1*dict_stn_metadata['n_stn']+s2] = p_sfc2_hr_s_df[dict_stn_metadata['stn_id'][s1]] - p_sfc2_hr_s_df[dict_stn_metadata['stn_id'][s2]]
                    column_str[s1*dict_stn_metadata['n_stn']+s2] = dict_stn_metadata['stn_id'][s1]+'-'+dict_stn_metadata['stn_id'][s2]
                    
            # write to master csv
            print      ('    write p_sfc_diff master begin ')
            logger.info('    write p_sfc_diff master begin ')
            p_sfc1_diff_hr_s_df = pd.DataFrame(p_sfc1_diff_hr_s, index=dt_axis, columns=column_str) 
            p_sfc1_diff_hr_s_df.to_csv(p_sfc1_diff_master_file) 
            p_sfc2_diff_hr_s_df = pd.DataFrame(p_sfc2_diff_hr_s, index=dt_axis, columns=column_str) 
            p_sfc2_diff_hr_s_df.to_csv(p_sfc2_diff_master_file) 
            print      ('    write p_sfc_diff master end ')   
            logger.info('    write p_sfc_diff master end ')   
            
            print      ('    p_sfc1_diff_hr_s min max is %5.2f %5.2f ' %(np.nanmin(p_sfc1_diff_hr_s), np.nanmax(p_sfc1_diff_hr_s)))
            logger.info('    p_sfc1_diff_hr_s min max is %5.2f %5.2f ' %(np.nanmin(p_sfc1_diff_hr_s), np.nanmax(p_sfc1_diff_hr_s)))
            print      ('    p_sfc2_diff_hr_s min max is %5.2f %5.2f ' %(np.nanmin(p_sfc2_diff_hr_s), np.nanmax(p_sfc2_diff_hr_s)))
            logger.info('    p_sfc2_diff_hr_s min max is %5.2f %5.2f ' %(np.nanmin(p_sfc2_diff_hr_s), np.nanmax(p_sfc2_diff_hr_s)))
    print      ('calc_pgrad end ')
    logger.info('calc_pgrad end ')



###############################################################################    
if __name__ == "__main__":

    #debug_mode = True
    debug_mode = False
    if not debug_mode: 
        # parse inputs 
        parser = argparse.ArgumentParser(description='argparse')
        parser.add_argument('--batch_mode',    type=str, help='operational or backfill', required=True, default='operational')
        parser.add_argument('--model_name',    type=str, help='gfs/nam/hrrr', required=False, default='hrrr')
        parser.add_argument('--process_name',  type=str, help='download/process_grib/process_csv/plot', required=True, default='download')    
        parser.add_argument('--bucket_name',   type=str, help='bucket_name', required=True, default='data')
        args = parser.parse_args()
        model_name    = args.model_name
        process_name  = args.process_name 
        batch_mode = args.batch_mode 
        bucket_name   = args.bucket_name    
    else:
        os.chdir('/home/csmith/pgrad')
        #model_name = 'hrrr'    
        #model_name = 'nam'    
        model_name = 'gfs'    
        batch_mode = 'operational'
        #batch_mode = 'backfill'
        #process_name = 'download'
        process_name = 'process_grib'
        #process_name = 'process_csv'
        #process_name = 'plot'
        bucket_name = 'data'
 
    # sanitize inputs
    model_name_list = ['gfs', 'nam', 'hrrr']
    if model_name not in model_name_list:
        print('ERROR model_name %s not supported' %(model_name))
        sys.exit()
    if process_name not in ['download', 'process_grib', 'process_csv', 'calc_pgrad', 'plot']:
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
    if debug_mode: 
        forecast_horizon_hr = 6
        
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
    
    if   batch_mode == 'operational':
        hours_to_backfill = 0
    elif batch_mode == 'backfill':
        hours_to_backfill = 24

    dt_init = dt_init_expected
    while dt_init >= dt_init_expected - td(hours=hours_to_backfill): 
        print      ('  processing init %s ' % (dt_init.strftime('%Y-%m-%d_%H-%M')))
        logger.info('  processing init %s ' % (dt_init.strftime('%Y-%m-%d_%H-%M')))
        print('executing process %s' %(process_name))
        if   process_name == 'download':
            download_data(model_name, dt_init, forecast_horizon_hr, bucket_name)
        elif process_name == 'process_grib':
            process_grib_data(model_name, dt_init, forecast_horizon_hr, bucket_name)
        elif process_name == 'process_csv':
            process_csv_data(model_name, dt_init, forecast_horizon_hr, bucket_name)
        elif process_name == 'calc_pgrad':
            calc_pgrad(model_name_list, dt_init, bucket_name)
        elif process_name == 'plot':
            plot_data(model_name, dt_init, forecast_horizon_hr, bucket_name)
        dt_init = dt_init - td(hours=update_frequency_hrs)
        
    # close log file
    print      ('close_logger begin ')
    logger.info('close_logger begin ')
    close_logger(logger, process_name, dt_start_lt, utc_conversion, time_zone_label) 

###############################################################################    




