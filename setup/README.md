
# pGrad setup readme

![alt text](../images/racecast_tech_stack.png "hover text")

## Table of Contents
1. [Instance Setup](README.md#Instance-Setup)
1. [Spark Cluster Setup](README.md#spark-cluster-setup)
1. [Connect Spark to Postgres](README.md#Connect-Spark-to-Postgres)

## Instance Setup

Spin up an EC2 instance.  I chose a Ubuntu t2.micro. 
Default 8 Gb of hard disk.
Allow ports ssh from home IP, HTTP and HTTPS.  
Add the keypair from local to the instance.
ssh into the instance and 

Intall Postgres and Apache webserver
```
sudo apt-get update && sudo apt upgrade && sudo apt-get install postgresql postgresql-contrib libpq-dev python3-psycopg2 apache2

```
and navigate to the IP address to check that Apache is running.

Clone the repo via https (not ssh)  

```
git clone https://github.com/weathertrader/pgrad.git
```

Install Python from miniconda.
```
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
chmod 755 Miniconda3-latest-Linux-x86_64.sh
Install the executable 
source ~/.bashrc

```

Install the environment (requirements.txt doesn't work yet)

```
conda update conda 
conda config --add channels conda-forge
# does not work
conda install -c conda-forge psycopg2 numpy pandas dask netCDF4 xarray spyder matplotlib
# works 
conda install -c conda-forge psycopg2 numpy pandas dask xarray matplotlib
# works on ubuntu, does not work on chromebook 
conda install -c conda-forge eccodes cfgrib
# works on chromebook 
sudo apt-get install libeccodes0
pip install cfgrib
python -m cfgrib selfcheck
cd pgrad
# pip install -r requirements.txt
```

Copy over the /aws folder with the following files
```
mkdir ~/aws
```

Backfill data from the last few forecast runs
```
src/backfill.sh
```
Once this done, go ahead and exectute an operational full ETL to make sure 
you have the latest data
```
src/operational.sh
```


Link the apache www directory to the repo www and 
navigate to the webpage and view the initial website at ip:/pgrad.html  

```
ln -s /home/ubuntu/pgrad/www /var/www/html
/home/user/pgrad/www has permissions 775

Check /home/user/www and /var/www/html owners
Apache user\group must have access to /home, /home/user and /home/user/www paths

Check Apache configuration:
look for FollowSymLinks option

<Directory /var/www/html>
    ...
    Options FollowSymLinks
</Directory>

/home/user to 711 and see if that helps any. Keep in mind... localhost/www won't exist unless you have a folder called www inside of the DocumentRoot.

Also, you're better off using ~/public_html over symlinking /var/www/html to something in your home directory. Bad practice/juju.


```



Install the crontab 



not needed
copy over a .bashrc with xyz environmental variables 


On the pg_server I install these into the system Python, 
but on local you may want to put them in a conda environment

NOT DONE YET 


NOT DONE YET 

conda create -n pg_env
conda activate pg_env
```
```





edium.  Set up a keypair from local to the pg server, and from the Spark master to the pg instance.

Check that you can ssh from master to pg, and from local to pg.  
ssh into pg and install postgres, dash and the python ORM to postgres

```
# check that master can ssh into pg 
ssh ubuntu@ec2-34-222-54-126.us-west-2.compute.amazonaws.com
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
Now create the pg user and database

```
sudo su postgres
psql
CREATE USER ubuntu WITH PASSWORD '';
CREATE DATABASE racecast WITH OWNER ubuntu;
\q
```
and execture the `create_db.py` script to make sure it works 
```
python src/create_db.py
```

Now cd to the postgres configuration directory and edit the IP's that postgres will allow and listen on 

```
cd /etc/postgresql/10/main
sudo cp postgresql.conf postgresql.conf_old
sudo vi /etc/postgresql/10/main/postgresql.conf
uncomment and set 
listen_addresses=’*’
```
and
```
sudo cp pg_hba.conf pg_hba.conf_old
sudo vi pg_hba.conf
# Near bottom of file after local rules, add rule (allows remote access):
host    all             all             0.0.0.0/0               md5
host    all		        all		        all			            trust
```
and restart the pg database

```
sudo /etc/init.d/postgresql restart
sudo /etc/init.d/postgresql status
```

Now check that the Spark master can also create tables on the pg database.  Remember to substitute the pg IP in the .bashrc db_host_name.
```
export db_host=ec2-34-222-54-126.us-west-2.compute.amazonaws.com
```
You can also test the connection from local if you postgres setup there
```
psql -U ubuntu -d racecast -p 5432 -h ec2-34-222-54-126.us-west-2.compute.amazonaws.com
```
and that should drop you into a psql prompt.

You can test in the Ipython console from local or Spark master using 

```
import os
import psycopg2
conn = psycopg2.connect(database=os.environ['db_name'], host='ec2-34-222-54-126.us-west-2.compute.amazonaws.com', user     = os.environ['db_user_name'], password=os.environ['db_password'], port=os.environ['db_port'])    
```
If this does not work you'll want to doublecheck your AWS security group Inbound settings

## Spark Cluster Setup

On the master and on all workers, install the following 

```
sudo apt-get update && sudo apt upgrade
sudo apt-get install openjdk-8-jre-headless
sudo apt-get install scala
scala -version # should return 2.11.12 or above
wget https://downloads.apache.org/spark/spark-2.4.5/spark-2.4.5-bin-hadoop2.7.tgz

tar -xvf spark-2.4.5-bin-hadoop2.7.tgz
sudo mv spark-2.4.5-bin-hadoop2.7/ /usr/local/spark
```

Now install a python environment which contains pyspark
```
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
chmod 775 that file and execute it then
source ~/.bashrc
conda update conda
conda config --add channels conda-forge
conda install -c conda-forge pyspark
```
On my local machine I use a conda environment for this 
```
conda create -n pyspark_env
conda activate pyspark_env
conda install -c conda-forge pyspark spyder‑kernels s3fs

```

and edit the following files 

```
vi ~/.profile
export PATH=/usr/local/spark/bin:$PATH
export PYSPARK_PYTHON=/home/ubuntu/miniconda3/bin/python3
export PYSPARK_DRIVER_PYTHON=/home/ubuntu/miniconda3/bin/python3
source ~/.profile
```

```
vi ~/.bashrc
export PYSPARK_PYTHON=/home/ubuntu/miniconda3/bin/python3
export PYSPARK_DRIVER_PYTHON=/home/ubuntu/miniconda3/bin/python3

on master 
export PATH=/usr/local/spark/bin:$PATH
export PYSPARK_PYTHON=/home/ubuntu/miniconda3/bin/python3
export PYSPARK_DRIVER_PYTHON=/home/ubuntu/miniconda3/bin/python3

on local
export PATH=/home/craigmatthewsmith/spark-2.4.5-bin-hadoop2.7/bin:$PATH
export PYSPARK_PYTHON=/home/craigmatthewsmith/anaconda3/envs/pyspark_env/bin/python3
export PYSPARK_DRIVER_PYTHON=/home/craigmatthewsmith/anaconda3/envs/pyspark_env/bin/python3
source  ~/.bashrc
```

```
vi /usr/local/spark/conf/spark-env.sh

on master
export SPARK_MASTER_HOST=ec2-54-202-214-49.us-west-2.compute.amazonaws.com
export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
export PYSPARK_PYTHON=/home/ubuntu/miniconda3/bin/python3
export PYSPARK_DRIVER_PYTHON=/home/ubuntu/miniconda3/bin/python3

on local
vi /usr/local/spark/conf/spark-env.sh
export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
export PYSPARK_PYTHON=/home/craigmatthewsmith/anaconda3/envs/pyspark_env/bin/python3
export PYSPARK_DRIVER_PYTHON=/home/craigmatthewsmith/anaconda3/envs/pyspark_env/bin/python3

```

and edit `~/.aws/config` and `~/.aws/credentials` as before

Also add the worker IPs to the configuration files 
```
vi /usr/local/spark/conf/slaves
ec2-18-237-177-6.us-west-2.compute.amazonaws.com
ec2-34-214-205-202.us-west-2.compute.amazonaws.com
ec2-34-215-182-26.us-west-2.compute.amazonaws.com
ec2-34-219-195-126.us-west-2.compute.amazonaws.com
ec2-34-214-104-123.us-west-2.compute.amazonaws.com
```

And restart the Spark cluster 
```
on Spark master
bash /usr/local/spark/sbin/start-all.sh
bash /usr/local/spark/sbin/stop-all.sh 
or on local without workers
bash ~/spark-2.4.5-bin-hadoop2.7/sbin/stop-master.sh 
bash ~/spark-2.4.5-bin-hadoop2.7/sbin/stop-slave.sh 
bash ~/spark-2.4.5-bin-hadoop2.7/sbin/start-master.sh 
```
The Spark web UI is availabe on port 8080
http://ec2-54-202-214-49.us-west-2.compute.amazonaws.com:8080


If the Spark cluster runs out of space remove the working application directories
```
rm -rf /usr/local/spark/work/app*
```

## Connect Spark to Postgres

Add the postgres jar to master and all workers
```
scp -i ~/.ssh/sundownerwatch-IAM-keypair.pem postgresql-42.2.14.jar ubuntu@ec2-54-202-214-49.us-west-2.compute.amazonaws.com://usr/local/spark/jars/.
scp -i ~/.ssh/sundownerwatch-IAM-keypair.pem postgresql-42.2.14.jar ubuntu@ec2-18-237-177-6.us-west-2.compute.amazonaws.com:/home/ubuntu/.
scp -i ~/.ssh/sundownerwatch-IAM-keypair.pem postgresql-42.2.14.jar ubuntu@ec2-34-214-205-202.us-west-2.compute.amazonaws.com:/home/ubuntu/.
scp -i ~/.ssh/sundownerwatch-IAM-keypair.pem postgresql-42.2.14.jar ubuntu@ec2-34-215-182-26.us-west-2.compute.amazonaws.com:/home/ubuntu/.
scp -i ~/.ssh/sundownerwatch-IAM-keypair.pem postgresql-42.2.14.jar ubuntu@ec2-34-219-195-126.us-west-2.compute.amazonaws.com:/home/ubuntu/.
scp -i ~/.ssh/sundownerwatch-IAM-keypair.pem postgresql-42.2.14.jar ubuntu@ec2-34-214-104-123.us-west-2.compute.amazonaws.com:/home/ubuntu/.
```







