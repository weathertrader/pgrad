
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

Backfill data from the last few forecast runs
```
src/backfill.sh
```
Once this done, go ahead and execute an operational full ETL to make sure 
you have the latest data
```
src/operational.sh
```


Link the apache www directory to the repo www and 
navigate to the webpage and view the initial website at ip:/pgrad.html  

```
cd /var/www/html
sudo ln -s ~/pgrad/www/pgrad.html .
sudo ln -s ~/pgrad/www/pgrad.js .
# sudo ln -s ~/pgrad/www/style.css .

cd /var/www
sudo ln -s ~/pgrad/images/ .
sudo ln -s ~/pgrad/top_events/ .


ln -s /var/www/* /ZFSRaidz/XBMC/Multimedia/Anime/Naruto_Shippuuden-2/
ln -s ~/code/notes/notes ~/bin/notes

sudo ln -s /home/ubuntu/pgrad/www/css /var/www/
sudo ln -s /home/ubuntu/pgrad/www/js /var/www/
sudo ln -s /home/ubuntu/pgrad/images /var/www/
sudo ln -s /home/ubuntu/pgrad/top_events /var/www/

sudo ln -s /home/ubuntu/pgrad/www/html/pgrad.html /var/www/html/

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

```
crontab src/crontab.txt
```


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
  
  
  
  
