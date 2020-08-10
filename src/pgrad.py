
'''
name: pgrad.py 
purpose: process and analyze pressure gradient forcing from NWP models 
author: Craig Smith, craig.matthew.smith@gmail.com
usage: ./src/run.sh n  where n is the number of batteries to analyze [1-5]
repo: https://github.com/weathertrader/battery_charge
'''

# Side project plan 
# write code for download to local
#                download to s3
# log to local 
# log to s3

# works for gfs, nam, and hrrr
# curl filter download 

# environment
# define station locations 
# write code to process 
# write code to plot static 
# code -> lambda, operationalize 
# station observations -> tables of top historical events 
# www deploy, infra, recovery 
# front end js static
# front end dynamic 


import os
import sys
import csv
import argparse 
import pandas as pd
import numpy as np
from datetime import datetime as dt 
from datetime import timedelta as td 
import glob
import requests

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
                url_folder_str = model_name+'.'+dt_init.strftime('%Y%m%d')+'/'+dt_init.strftime('%H')                
                file_name_remote = model_name+'.t'+dt_init.strftime('%H')+'z.pgrb2.0p25.f'+str(hr).zfill(3)
                url_temp = base_url+url_folder_str+'/'+file_name_remote
            print      ('    url_temp is %s ' % (url_temp))
            logger.info('    url_temp is %s ' % (url_temp))
  
            #response = requests.head(url_temp+'no')
            response = requests.head(url_temp)
            #response.headers
            if response.status_code != 200: # 404 not found
                file_exists_on_remote = False
                print      ('    file does not exist on remote')
                logger.info('    file does not exist on remote')
            else:             
    
curl_dl_command = 'curl '+url_temp+' -o '+file_name_temp_ingest
print      ('    download_forecast_grid_and_write_to_local: curl_dl_command is %s ' % (curl_dl_command))
logger.info('    download_forecast_grid_and_write_to_local: curl_dl_command is %s ' % (curl_dl_command)) 
process_check = subprocess.Popen(curl_dl_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
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
                
    
    
    
    
    import subprocess
    debug_local_function = False

    file_exists_on_remote = False    
    curl_check_command = 'curl -I '+url_temp
    if (debug_local_function):
        print      ('    check_if_file_exists_on_remote_server: curl_check_command is %s ' % (curl_check_command))
        logger.info('    check_if_file_exists_on_remote_server: curl_check_command is %s ' % (curl_check_command)) 
    process_check = subprocess.Popen(curl_check_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out,err = process_check.communicate(timeout=10) # 10 s   
    out_str = str(out)
    # note csmith, this or other if statement is for ftp vs http
    #if   (process_check.returncode == 0):  
    #elif (process_check.returncode != 0): # file does not exist 
    
    if (url_temp.startswith('ftp')):
        if   (('Given file does not exist' in out_str) or ('Server denied you to change to the given directory' in out_str)): 
            # file exists 
            file_exists_on_remote = False
        else:    
            file_exists_on_remote = True
            # "b'  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current\\n                                 Dload  Upload   Total   Spent    Left  Speed\\n\\r  0     0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0\\r  0 22.7M    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0\\nLast-Modified: Sun, 13 Jan 2019 14:11:54 GMT\\r\\nContent-Length: 23900160\\r\\nAccept-ranges: bytes\\r\\n'"        
            if (debug_local_function):
                print      ('    check_if_file_exists_on_remote_server: file exists ')
                logger.info('    check_if_file_exists_on_remote_server: file exists ')
    elif (url_temp.startswith('http')):        
        if   ('200 OK' in out_str): # file exists 
            file_exists_on_remote = True
            if (debug_local_function):
                print      ('    check_if_file_exists_on_remote_server: file exists ')
                logger.info('    check_if_file_exists_on_remote_server: file exists ')
        elif ('404 Not Found' in out_str):  # file does not exist 
            file_exists_on_remote = False
            print      ('    check_if_file_exists_on_remote_server: file does not exist')
            logger.info('    check_if_file_exists_on_remote_server: file does not exist')
            print      ('    check_if_file_exists_on_remote_server: process_check.returncode is %s' %(process_check.returncode)) 
            logger.info('    check_if_file_exists_on_remote_server: process_check.returncode is %s' %(process_check.returncode)) 
            print      ('    check_if_file_exists_on_remote_server: out is %s' %(out)) 
            logger.info('    check_if_file_exists_on_remote_server: out is %s' %(out)) 
            print      ('    check_if_file_exists_on_remote_server: err is %s' %(err)) 
            logger.info('    check_if_file_exists_on_remote_server: err is %s' %(err)) 
  
    
  
            (file_final_exists_on_remote)   = check_if_file_exists_on_remote_server(logger, url_final)
            if not (file_final_exists_on_remote):
            else: 
                print      ('  check_forecast_availability: file exists on remote %s ' % (url_final))
                logger.info('  check_forecast_availability: file exists on remote %s ' % (url_final))
                forecast_available = True
  
    
            return url_temp            
            
        
        
        
            
            file_exists_on_remote
            # if it exists, then download it
            # if it does not exist, then break since no further will be avail 
            
        print      ('    looking for %s and %s ' % (file_name_ingest, file_name_processed))
        logger.info('    looking for %s and %s ' % (file_name_ingest, file_name_processed))

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
    model_name = 'gfs'    
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
        dt_init = dt_init - td(hours=update_frequency_hrs)
        print('executing process %s' %(process_name))
        if   process_name == 'download':
            download_data(model_name, dt_init, forecast_horizon_hr, bucket_name)
        elif process_name == 'process':
            process_data(model_name, dt_init, forecast_horizon_hr, bucket_name)
        if   process_name == 'plot':
            plot_data(model_name, dt_init, forecast_horizon_hr, bucket_name)
        
    # close log file
    print      ('close_logger begin ')
    logger.info('close_logger begin ')
    close_logger(logger, process_name, dt_start_lt, utc_conversion, time_zone_label) 

###############################################################################    




