
"""Example DAG demonstrating the usage of the BashOperator."""

from datetime import timedelta

from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.utils.dates import days_ago

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': days_ago(2),
    'catchup_by_default': False
    # 'email': ['airflow@example.com'],
    # 'email_on_failure': False,
    # 'email_on_retry': False,
    # 'retries': 1,
    # 'retry_delay': timedelta(minutes=5),
    # 'queue': 'bash_queue',
    # 'pool': 'backfill',
    # 'priority_weight': 10,
    # 'end_date': datetime(2016, 1, 1),
    # 'wait_for_downstream': False,
    # 'dag': dag,
    # 'sla': timedelta(hours=2),
    # 'execution_timeout': timedelta(seconds=300),
    # 'on_failure_callback': some_function,
    # 'on_success_callback': some_other_function,
    # 'on_retry_callback': another_function,
    # 'sla_miss_callback': yet_another_function,
    # 'trigger_rule': 'all_success'
}

# */5 * * * *

dag_01 = DAG(
    dag_id='id_01',
    default_args=default_args,
    description='desc_01',
    schedule_interval='5  * * * *',    
    dagrun_timeout=timedelta(minutes=20),
    catchup=False,
    tags=['01'])
#    schedule_interval='11  * * * *',    
dag_11 = DAG(
    dag_id='id_11',
    default_args=default_args,
    description='desc_11',
    schedule_interval='6  * * * *',    
    dagrun_timeout=timedelta(minutes=20),
    catchup=False,
    tags=['11'])
dag_21 = DAG(
    dag_id='id_21',
    default_args=default_args,
    description='desc_21',
    schedule_interval='9 * * * *',    
    dagrun_timeout=timedelta(minutes=20),
    catchup=False,
    tags=['21'])
dag_31 = DAG(
    dag_id='id_31',
    default_args=default_args,
    description='desc_31',
    schedule_interval='13 * * * *',    
    dagrun_timeout=timedelta(minutes=20),
    catchup=False,
    tags=['31'])
dag_56 = DAG(
    dag_id='id_56',
    default_args=default_args,
    description='desc_56',
    schedule_interval='17 * * * *',    
    dagrun_timeout=timedelta(minutes=20),
    catchup=False,
    tags=['56'])

task_cleanup = BashOperator(
    task_id='id_cleanup',
    bash_command='~/pgrad/src/cron_scripts/cleanup.bsh',
    dag=dag_01)

task_plot_data = BashOperator(
    task_id='id_plot_data',
    bash_command='~/pgrad/src/cron_scripts/plot_data.bsh',
    dag=dag_56)

task_download_hrrr = BashOperator(
    task_id='id_download_hrrr',
    bash_command='~/pgrad/src/cron_scripts/download_hrrr.bsh',
    dag=dag_11)
task_process_grib_hrrr = BashOperator(
    task_id='id_process_grib_hrrr',
    bash_command='~/pgrad/src/cron_scripts/process_grib_hrrr.bsh',
    dag=dag_11)
task_process_csv_hrrr = BashOperator(
    task_id='id_process_csv_hrrr',
    bash_command='~/pgrad/src/cron_scripts/process_csv_hrrr.bsh',
    dag=dag_11)
task_calc_pgrad_hrrr = BashOperator(
    task_id='id_calc_pgrad_hrrr',
    bash_command='~/pgrad/src/cron_scripts/calc_pgrad_hrrr.bsh',
    dag=dag_11)

task_download_nam = BashOperator(
    task_id='id_download_nam',
    bash_command='~/pgrad/src/cron_scripts/download_nam.bsh',
    dag=dag_21)
task_process_grib_nam = BashOperator(
    task_id='id_process_grib_nam',
    bash_command='~/pgrad/src/cron_scripts/process_grib_nam.bsh',
    dag=dag_21)
task_process_csv_nam = BashOperator(
    task_id='id_process_csv_nam',
    bash_command='~/pgrad/src/cron_scripts/process_csv_nam.bsh',
    dag=dag_21)
task_calc_pgrad_nam = BashOperator(
    task_id='id_calc_pgrad_nam',
    bash_command='~/pgrad/src/cron_scripts/calc_pgrad_nam.bsh',
    dag=dag_21)

task_download_gfs = BashOperator(
    task_id='id_download_gfs',
    bash_command='~/pgrad/src/cron_scripts/download_gfs.bsh',
    dag=dag_31)
task_process_grib_gfs = BashOperator(
    task_id='id_process_grib_gfs',
    bash_command='~/pgrad/src/cron_scripts/process_grib_gfs.bsh',
    dag=dag_31)
task_process_csv_gfs = BashOperator(
    task_id='id_process_csv_gfs',
    bash_command='~/pgrad/src/cron_scripts/process_csv_gfs.bsh',
    dag=dag_31)
task_calc_pgrad_gfs = BashOperator(
    task_id='id_calc_pgrad_gfs',
    bash_command='~/pgrad/src/cron_scripts/calc_pgrad_gfs.bsh',
    dag=dag_31)

task_download_gfs  >> task_process_grib_gfs  >> task_process_csv_gfs  >> task_calc_pgrad_gfs 
task_download_nam  >> task_process_grib_nam  >> task_process_csv_nam  >> task_calc_pgrad_nam 
task_download_hrrr >> task_process_grib_hrrr >> task_process_csv_hrrr >> task_calc_pgrad_hrrr 

#run_this_last = DummyOperator(
#    task_id='run_this_last',
#    dag=dag)
#run_this = BashOperator(
#    task_id='run_after_loop',
#   bash_command='echo 1',
#    dag=dag)

#for i in range(3):
#    task = BashOperator(
#        task_id='runme_' + str(i),
#        bash_command='echo "{{ task_instance_key_str }}" && sleep 1',
#        dag=dag)
#    task >> run_this

#also_run_this = BashOperator(
#    task_id='also_run_this',
#    bash_command='echo "run_id={{ run_id }} | dag_run={{ dag_run }}"',
#    dag=dag)
# [END howto_operator_bash_template]

#run_this >> run_this_last
#also_run_this >> run_this_last

if __name__ == "__main__":
    dag.cli()