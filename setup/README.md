
# pgrad setup readme

## Table of Contents
1. [Instance Setup](README.md#Instance-Setup)
1. [Spark Cluster Setup](README.md#spark-cluster-setup)
1. [Connect Spark to Postgres](README.md#Connect-Spark-to-Postgres)

## Instance Setup

Spin up an EC2 instance.  I chose a t2.micro with Ubuntu 20.04. 
Default 8 Gb of hard disk.
Allow ports ssh from home IP, HTTP and HTTPS.  
Add the keypair from local to the instance.
ssh into the instance and 

Intall Postgres and Apache webserver
```
sudo apt-get update && sudo apt upgrade && sudo apt-get install build-essential postgresql postgresql-contrib libpq-dev python3-psycopg2 apache2 libeccodes0
```
and navigate to the IP address to view the default index.html and check that Apache is running.

Clone the repo via https (not ssh)  
```
git clone https://github.com/weathertrader/pgrad.git
```

Install Python from miniconda.  After changing permissions on the executable, execute it and source the new environment.
```
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
chmod 755 Miniconda3-latest-Linux-x86_64.sh
source ~/.bashrc
```

Install the environment from scratch or from the requirements.txt

```
pip install -r pgrad/requirements.txt
```
To recreate the environment and requirements.txt you can also use this 
```
pip install numpy pandas dask netCDF4 xarray spyder matplotlib cfgrib flask apache-airflow
# check cfgrib installation
python -m cfgrib selfcheck
pip freeze > requirements.txt
```

Backfill data from the last few forecast runs.  I suggest backgrounding this process 
as it will likely take 30 min or so.
```
src/backfill.sh&
```

The data pipelines can be operationalized using the provided crontab 
```
crontab src/crontab.txt
```
or using Apache Airflow, which can be installed by adding the following to the `/.bashrc`
```
export AIRFLOW_HOME=~/airflow
```
and edit the `airflow.cfg` config file and set
```
dags_folder = ~/pgrad/dags
load_examples = False
catchup_by_default = False
```
Then initialize the db and run the scheduler and webserves as daemons.  
```
airflow initdb
airflow scheduler -D
airflow webserver -D
```
Browse to port 8080 on your EC2 instance and turn the dags on 
dags at `http://localhost:8080/admin/`.
You can view and test the active dags using 
```
airflow list_dags
airflow list_tasks id_21
airflow list_tasks id_21 --tree
airflow test id_21 download_grib_nam 2015-01-01
```
In case you need to reset or kill airflow you can use the following
```
airflow resetdb
more ~/airflow/airflow-webserver.pid
ps -aux | grep airflow
kill -9 pid
```
Most of these ETLs are set to run hourly and their logs can be viewed at `logs/log*txt`.
You can also view their performance over time via a command such as
```
tail -n 2 logs/log_download_gfs_*txt
```
Logs are rotated after 7 days and that can be edited in `src/pgrad.py` with the 
`n_days_to_retain` variable.

In case of debugging needs, it's also possible to run through all operational ETL's using  
```
src/operational.sh
```

Next task is to set the webserver to read the repo web pages.
Link the apache `www/html` directory to the repo `www/html` and 
navigate to the webpage and view the initial website at ip://pgrad.html  
```
cd /var/www/html
sudo ln -s ~/pgrad/www/html/pgrad.html .
sudo ln -s ~/pgrad/www/html/pgrad.js .
# sudo ln -s ~/pgrad/www/style.css .
sudo ln -s ~/pgrad/images/ .
sudo ln -s ~/pgrad/top_events/ .
```
Note that the images directory contains the images that are updated hourly
and the top_events images are included in the repo and do not be updated 
outside of that.



##############################################################################
BELOW NOT ORGANIZED YET 

NOT NEEDED 
copy over a .bashrc with xyz environmental variables 

NOT DONE YET 


NOT DONE YET 

conda create -n pg_env
conda activate pg_env
```
```
Copy over the /aws folder with the following files
```
mkdir ~/aws
```

Follow the directions in the main repo README.md to set up a PG user, database and edit your .bashrc with appropriate environmental variables.
Also be sure to add AWS credentials to your `.profile` and `.aws` files

```
vi ~/.profile 
export AWS_ACCESS_KEY_ID=
export AWS_SECRET_ACCESS_KEY=

and
mkdir .aws

vi .aws/config
[default]
region = us-west-2

vi .aws/credentials
[credentials]
aws_access_key_id=
aws_secret_access_key=

```
  
Not needed 
/home/user/pgrad/www has permissions 775
Check /home/user/www and /var/www/html owners
Apache user\group must have access to /home, /home/user and /home/user/www paths

Check Apache configuration:
look for FollowSymLinks option
<Directory /var/www/html>
    ...
    Options FollowSymLinks
</Directory>

can chmod to 755 or 711

 
  
  
  
  
