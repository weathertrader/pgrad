
# RaceCast 

Live broadcasts of athletes positions during races from gps streaming data using Spark mini-batch processing, Postgres and Dash.

![alt text](images/racecast_intro.png "hover text")

## Table of Contents

1. [Motivation and Requirements](README.md#motivation-and-requirements)
1. [RaceCast Website](README.md#racecast-website)
1. [Dataset](README.md#dataset)
1. [Architecture](README.md#architecture)
1. [Scaling](README.md#scaling)
1. [Setup](README.md#setup)
1. [Data Preprocessing](README.md#Data-preprocessing)
1. [Installation](README.md#installation)
1. [Set up database tables](README.md#set-up-database-tables)
1. [Spark Batch Run Instructions](README.md#Spark-Batch-Run-Instructions)
1. [Web App Instructions](README.md#Web-App-Instructions)

## Motivation and Requirements

During an athletic race, spectators would like to know who is the lead and by how much, and 
they would also like to be able get the position of their favorite runner in realtime.
The end goal was a leaderboard which updates at least every minute that is 
capable of processing up to 100K participants.
During the course of this project I specifically sought to test the limitations of a Spark min-batching approach.

## RaceCast Website 

The leaderboard website I built has a race leaderboard table, and figure showing the progress of all of the leaders,
a text box where the end-user can search for their runner, a text box which shows the details of their runner in 
terms of last reported location and distance traveled, and a figure showing progress of their specific runner.

![alt text](images/racecast_website.png "hover text")

## Dataset

The dataset I used is the Endomondo GPS Tracks, which has 167K unique activities with average duration of 1 hour and average reporting frequency of once every 10 seconds.
I mocked all the tracks to start at the same location and integrated GPS coordinates over time to get distance traveled.
The records looked like this

```
record, time_elapsed, userid, lon, lat, heart_rate
3916,0,3790,0.0,0.0,78
3917,0,3856,0.0,0.0,145
3918,1,34,0.00238,0.0023,101
3919,1,876,0.00164,0.0043,123
```

## Architecture 

For this project I used S3, Apache Spark, Airflow, Postgres and Plotly Dash, all hosted on AWS EC2 instances.  
For further information on the setup please see the `setup/README.md`.

![alt text](images/racecast_tech_stack.png "hover text")

## Scaling

I first tested the performance of the Spark jobs varies across the number of Spark workers used.  
I found very good scaling at low number of workers, and a performance degradation for larger number of instances.

![alt text](images/spark_timing_vs_instances.png "hover text")

Next I tested throughput of total number of records per second according to the number of athletes that participated in the event.
At very large number of participants it is likely that throughput performance will be begin to asymptote, but the 
system that I designed was quite a ways away from that mark.

![alt text](images/spark_throughput_vs_athlete.png "hover text")

One of the key steps I did to make my Spark jobs faster was to define rather than infer Schema.  
By defining the schema, I was able to lower my read time down to 2 seconds, thus obviating any motivation for looking at Avro or Parquet.
I also decreased the job run-time of the Spark jobs through optimizing SQL joins .

The system as it's designed is very capable of handling up to 100K participants with sub-minute refresh rate. 
The slide deck associated with the project is available here [Link](https://docs.google.com/presentation/d/1adAMNAweJTesi1wBvob6it1NHg30EQTFziq98p7KOAU/edit?usp=sharing)

## Setup

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
