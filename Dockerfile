#####################################
# flask and cron container working on now 
FROM continuumio/miniconda3
# RUN apt-get update && apt-get -y install cron curl vim htop systemd
RUN apt-get update && apt-get -y install cron curl vim htop
ENV HOME /.
WORKDIR /pgrad
COPY . .

RUN conda update -y -n base -c defaults conda
RUN conda env create -f environment.yml

###########################
# option 1 works from cli, does not work from cron since bash has no bashrc to source
ENV PATH /opt/conda/envs/env_pgrad/bin:$PATH
# RUN /bin/bash -c "source activate env_pgrad"
###########################
# option 2 - have not tried yet
# ENV PATH /opt/conda/envs/env_pgrad/bin:$PATH
# RUN echo "source activate env_pgrad" > ~/.bashrc

#####################################
# my cron - works
RUN touch /var/log/cron.log
RUN crontab ~/pgrad/src/crontab.txt
CMD service cron start && tail -f /var/log/cron.log

# does not work
#RUN service cron start
# does not work
# CMD service cron start
# RUN cron
# CMD tail -f /var/log/cron.log
# does not work
# CMD ["cron", "-f"]
# does not work
# ENTRYPOINT ["service" "cron" "start"]
# does not work
# CMD ["service" "cron" "start"]
# CMD ["tail" "-f" "/var/log/cron.log"]

#ENTRYPOINT service cron start
#CMD tail -f /var/log/cron.log

# CMD ["/bin/bash" "service" "cron" "start" "&&" "tail" "-f" "/var/log/cron.log"]
#CMD ["service" "cron" "start" "&&" "tail" "-f" "/var/log/cron.log"]


# does not work
# RUN conda init bash

# RUN conda init bash && conda activate env_pgrad
# RUN conda activate env_pgrad

# pip 
# COPY requirements.txt requirements.txt
# COPY . .
# RUN pip3 install -r requirements.txt

# FROM debian:latest
# FROM python:3.7.10-buster
# RUN apt-get update && apt-get -y install cron curl vim python3-venv python3-pip

# RUN pip install poetry

# RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python3 -
# RUN poetry self update

# CMD ["bash"]


#####################################
# flask container works 
#FROM python:3.8-slim-buster
#WORKDIR /app
#COPY requirements.txt requirements.txt
#RUN pip3 install -r requirements.txt
#COPY . .
#CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]

#FROM ubuntu:latest

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
