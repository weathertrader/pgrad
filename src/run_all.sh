#!/bin/bash
#
sleep_interval=5
#echo $sleep_interval

# from s3
#python3 src/update_db.py s3://gps-data-processed/gps_batch_0.csv start
#sleep $sleep_interval

#mode=operational
mode=backfill
#anothervar=Fred
echo $mode 
#echo $myvariable $anothervar

#python ./src/pgrad.py --model_name=gfs --process_name=process_csv --bucket_name=data --batch_mode=$mode

################################
# gfs
python ./src/pgrad.py --model_name=gfs --process_name=download --bucket_name=data --batch_mode=$mode
python ./src/pgrad.py --model_name=gfs --process_name=process_grib --bucket_name=data --batch_mode=$mode
python ./src/pgrad.py --model_name=gfs --process_name=process_csv --bucket_name=data --batch_mode=$mode

# hrrr
python ./src/pgrad.py --model_name=hrrr --process_name=download --bucket_name=data --batch_mode=$mode
python ./src/pgrad.py --model_name=hrrr --process_name=process_grib --bucket_name=data --batch_mode=$mode
python ./src/pgrad.py --model_name=hrrr --process_name=process_csv --bucket_name=data --batch_mode=$mode
 
# nam 
python ./src/pgrad.py --model_name=nam --process_name=download --bucket_name=data --batch_mode=$mode
python ./src/pgrad.py --model_name=nam --process_name=process_grib --bucket_name=data --batch_mode=$mode
python ./src/pgrad.py --model_name=nam --process_name=process_csv --bucket_name=data --batch_mode=$mode

python ./src/pgrad.py --process_name=calc_pgrad --bucket_name=data --batch_mode=$mode
python ./src/pgrad.py --process_name=plot_data --bucket_name=data --batch_mode=$mode

# obs download
# obs_historical_download
# python ./src/pgrad.py --model_name=gfs --process_name=obs_historical_download --bucket_name=data --batch_mode=operational

# gfs operational download
# python ./src/pgrad.py --model_name=gfs --process_name=download --bucket_name=data --batch_mode=operational

# operational 
#python ./src/pgrad.py --process_name=calc_pgrad --bucket_name=data --batch_mode=operational
#python ./src/pgrad.py --process_name=plot_data --bucket_name=data --batch_mode=operational

# backfill 
#python ./src/pgrad.py --process_name=calc_pgrad --bucket_name=data --batch_mode=backfill
#python ./src/pgrad.py --process_name=plot_data --bucket_name=data --batch_mode=backfill


