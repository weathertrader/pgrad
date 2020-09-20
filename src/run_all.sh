#!/bin/bash
#
sleep_interval=5
#echo $sleep_interval

# from s3
#python3 src/update_db.py s3://gps-data-processed/gps_batch_0.csv start
#sleep $sleep_interval

# gfs
#python ./src/pgrad.py --model_name=gfs --process_name=download --bucket_name=data --batch_mode=operational
python ./src/pgrad.py --model_name=gfs --process_name=process_grib --bucket_name=data --batch_mode=operational
python ./src/pgrad.py --model_name=gfs --process_name=process_csv --bucket_name=data --batch_mode=operational

# hrrr
#python ./src/pgrad.py --model_name=hrrr --process_name=download --bucket_name=data --batch_mode=operational
python ./src/pgrad.py --model_name=hrrr --process_name=process_grib --bucket_name=data --batch_mode=operational
python ./src/pgrad.py --model_name=hrrr --process_name=process_csv --bucket_name=data --batch_mode=operational
 
# nam 
#python ./src/pgrad.py --model_name=nam --process_name=download --bucket_name=data --batch_mode=operational
python ./src/pgrad.py --model_name=nam --process_name=process_grib --bucket_name=data --batch_mode=operational
python ./src/pgrad.py --model_name=nam --process_name=process_csv --bucket_name=data --batch_mode=operational

python ./src/pgrad.py --process_name=calc_pgrad --bucket_name=data --batch_mode=operational
#python ./src/pgrad.py --process_name=plot_data --bucket_name=data --batch_mode=operational

