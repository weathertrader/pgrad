#####################################
# flask container works 
#FROM python:3.8-slim-buster
#WORKDIR /app
#COPY requirements.txt requirements.txt
#RUN pip3 install -r requirements.txt
#COPY . .
#CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]

#####################################
# flask and cron container working on now 
#FROM ubuntu:latest
FROM debian:latest
#RUN apt-get update && apt-get -y install cron 
RUN apt-get update && apt-get -y install cron curl vim python3-venv python3-pip

ENV HOME /.
WORKDIR /pgrad
COPY requirements.txt requirements.txt
COPY . .

#####################################
# my cron 
RUN crontab ~/pgrad/src/crontab.txt
RUN touch /var/log/cron.log 
CMD cron && tail -f /var/log/cron.log
# CMD ["cron", "-f"]


# RUN pip3 install -r requirements.txt


#####################################
# cron example 
# Copy hello-cron file to the cron.d directory
# COPY hello-cron /etc/cron.d/hello-cron 
# Give execution rights on the cron job
# RUN chmod 0644 /etc/cron.d/hello-cron
# Apply cron job
# RUN crontab /etc/cron.d/hello-cron 
# Create the log file to be able to run tail
# RUN touch /var/log/cron.log 
# Run the command on container startup
# CMD cron && tail -f /var/log/cron.log
# CMD ["cron", "-f"]


#FROM python:3.9.2-buster
#ENV PYTHONUNBUFFERED=1
#COPY . /code/
#FROM python:3.7-alpine
#WORKDIR /code
#ENV FLASK_APP=app.py
#ENV FLASK_RUN_HOST=0.0.0.0
#RUN apk add --no-cache gcc musl-dev linux-headers
#COPY requirements.txt requirements.txt
#RUN pip install -r requirements.txt
#EXPOSE 5000
#COPY . .
#CMD ["flask", "run"]


# cron based 
# RUN apt-get -y update && apt-get -y upgrade
# RUN apt-get install -y cron postgresql-client
# RUN touch /var/log/cron.log
# RUN mkdir /code
# WORKDIR /code
# ADD . /code/
# COPY crontab_simple.txt /etc/cron.d/cjob
# RUN chmod 0644 /etc/cron.d/cjob
# ENV PYTHONUNBUFFERED 1
# CMD cron -f

# docker build . 