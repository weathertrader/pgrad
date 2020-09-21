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


#mode = 'operational'
#echo $mode
#echo '$mode'
#echo "$mode"
#mode = 4 
#"operational"
#echo $mode
#echo '$mode'
#echo "$mode"

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

