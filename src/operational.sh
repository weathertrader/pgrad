#!/bin/bash
#
mode=operational
#mode=backfill
# cleanup
python ./src/pgrad.py --process_name=cleanup --bucket_name=data
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
# calc_pgrad
python ./src/pgrad.py --process_name=calc_pgrad --bucket_name=data --batch_mode=$mode
# plot
python ./src/pgrad.py --process_name=plot_data --bucket_name=data 

