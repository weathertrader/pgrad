
# pgrad.io

Operational pressure differences from key weather stations on the West Coast are often
used a rubrics for the strenght of various wind events such as Sundowners and Diablo winds.

![alt text](images_repo/sample_time_series.png "hover text")

## Table of Contents

1. [Website](README.md#website)
1. [Dataset](README.md#dataset)
1. [Stations](README.md#stations)
1. [Architecture and Setup](README.md#architecture-and-setup)
1. [Data Preprocessing](README.md#Data-preprocessing)
1. [Installation](README.md#installation)
1. [Set up database tables](README.md#set-up-database-tables)
1. [Spark Batch Run Instructions](README.md#Spark-Batch-Run-Instructions)
1. [Web App Instructions](README.md#Web-App-Instructions)

## Website 

The website is currently only available inside a VPN.  Public release is 
slated for 11/01/2020.

## Dataset

Observational data consists of surface observations pulled in via MesoWest API.
Model consists of operational runs updated 4x day of the following NWS models:
GFS - 10 day forecast horizon
NAM - 60 hr forecast horizon
HRRR - 36 hr forecast horizon 

## Stations

Pressure differences are calculated from stations pairs shown below.  
Feel free to suggest more.

![alt text](images_repo/sample_time_series.png "hover text")

## Architecture and Setup


Project currently on a t1 instance on AWS with no additional hard disk.
ETLs are written in bash and python using cron jobs, and the website is served with Apache.
The `src/crontab.txt` contains details of all jobs that are run and 
the setup readme has additional details.
https://github.com/weathertrader/pgrad/tree/master/setup

![alt text](images/racecast_tech_stack.png "hover text")


Spin up 5 EC2 t2.medium instances.  Install Spark on 6 of them, with one master and 6 workers.
On the 7th install postgres and dash and ensure communication between Spark and postgres.
Detailed setup directions can be found in the `setup/README.md` [Link](https://github.com/weathertrader/raceCast/tree/master/setup)

Inline-style: 
![alt text](images/racecast_tech_stack.png "hover text")



## Data Preprocessing 

Download the FitRec dataset `endomondoHR_proper.json` from [this website](https://sites.google.com/eng.ucsd.edu/fitrec-project/home) and move it the `data` directory.
Since the data file contains more activities than Spark can handle, we will split the file by activities and order them by time. 

```
src/run_preprocess_split.sh
```
then upload all of the data files and our processing scripts to a remote server on ec2 since we will process them there
```
scp -i ~/.ssh/sundownerwatch-IAM-keypair.pem src/* ec2-34-222-54-126.us-west-2.compute.amazonaws.com:/home/ubuntu/raceCast/src/.
scp -i ~/.ssh/sundownerwatch-IAM-keypair.pem data/gps_tracks_subset_by_activity_*.txt ec2-34-222-54-126.us-west-2.compute.amazonaws.com:/home/ubuntu/raceCast/data/.

```
and order the activities by time by running the following 
```
ssh -i ~/.ssh/sundownerwatch-IAM-keypair.pem ec2-34-222-54-126.us-west-2.compute.amazonaws.com
cd raceCast
src/run_preprocess.sh
```
which will write the gps data ordered by timestamp to s3. Since this pre-processing script will take a while it's best to launch it inside a `screen`.
 If you wish to verify the timestamp ordering you can do so with the following on a locally hosted file 
```
head -n 5 gps_stream_total_activities_001_dt_*.csv
tail -n 5 gps_stream_total_activities_001_dt_*.csv
```
## Set up database tables

On the postgres server create the db user and the database (see setup/README.md), then run the `create_db.py` script to set up the database tables 
```
scp -i ~/.ssh/sundownerwatch-IAM-keypair.pem src/* ec2-34-222-54-126.us-west-2.compute.amazonaws.com:/home/ubuntu/raceCast/src/.
ssh -i ~/.ssh/sundownerwatch-IAM-keypair.pem ec2-34-222-54-126.us-west-2.compute.amazonaws.com
python src/create_db.py
```
note that you will have to edit and source your .bashrc with the following environmental variables
```
vi .bashrc
export db_name=racecast
export db_host=localhost
export db_user_name=ubuntu
export db_password=''
export db_port=5432
```

and also check that this script works from the Spark master 

```
scp -i ~/.ssh/sundownerwatch-IAM-keypair.pem src/create_db.py ubuntu@ec2-54-202-214-49.us-west-2.compute.amazonaws.com:/home/ubuntu/raceCast/src/.
ssh -i ~/.ssh/sundownerwatch-IAM-keypair.pem ubuntu@ec2-54-202-214-49.us-west-2.compute.amazonaws.com
python src/create_db.py
```
note that in the .bashrc the db_host should now be the ip of the database server 
```
vi .bashrc
export db_host=ec2-34-216-105-134.us-west-2.compute.amazonaws.com
```

## Spark Batch Run Instructions 

ssh into the Spark master, spin up the cluster and ensure all workers are set up and have access to S3 etc and process the gps data using the following

```
src/run_batch_process_gps.sh
```
which will insert processed data into the `checkpoints` table on the postgres server.

## Web App Instructions 

Edit the last line in `dash/dash_app.py` to server the app over local or ec2 pg instance and launch the web app with 
```
python dash/dash_app.py 
```
and browse to 
```
http://127.0.0.1:8050/
or
http://ec2-34-222-54-126.us-west-2.compute.amazonaws.com:8050/
```
