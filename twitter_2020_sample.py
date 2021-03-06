from datetime import timedelta,datetime
# The DAG object; we'll need this to instantiate a DAG
from airflow import DAG
# Operators; we need this to operate!
from airflow.operators.python_operator import PythonOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.utils.dates import days_ago
from datetime import datetime
import requests
import json
import pandas as pd
import pymongo
import time
from datetime import date
from airflow.models import Variable
# These args will get passed on to each operator
# You can override them on a per-task basis during operator initialization

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2020,3,12,2,0,0),
    'email': ['airflow@example.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=1),
    # 'queue': 'bash_queue',
    # 'pool': 'backfill',
    # 'priority_weight': 10,
    # 'end_date': datetime(2016, 1, 1),
    # 'wait_for_downstream': False,
    # 'dag': dag,
    # 'sla': timedelta(hours=2),
    'execution_timeout': timedelta(minutes=300),
    # 'on_failure_callback': some_function,
    # 'on_success_callback': some_other_function,
    # 'on_retry_callback': another_function,
    # 'sla_miss_callback': yet_another_function,
    # 'trigger_rule': 'all_success'
}
dag = DAG(
    'twitter_2020_sample',
    default_args=default_args,
    description='sample 2020 twitter data',
    schedule_interval='@once',
)

dbase='POTUS_2020_DEV'
url1 = 'mongodb://%s:%s@denver.ischool.syr.edu'
mongoClient= pymongo.MongoClient(url1 % ('bitslab', '0rang3!'))
db = mongoClient[dbase]
col=db["tw_post_dev"]
data=[]

def get_data(ds, **kwargs):
    sample=[]
    start_date=Variable.get('sample_start_date')
    end_date=Variable.get('sample_end_date')
    sample_size=Variable.get('sample_size')
    for doc in col.aggregate([ { "$match": {"created_at":{"$gte":start_date,"$lte":end_date}} },{ "$sample": { "size": int(sample_size) } } ]):
        print(len(sample))
        doc['tweet_id']='ID_'+doc['tweet_id']
        sample.append(doc)
    df=pd.DataFrame(sample)
    df.to_csv("./home/jay/samples/twitter/twitter_posts_"+str(sample_size)+"_"+start_date+"--"+end_date+".csv")
    return "done"

get_data_step = PythonOperator(
    task_id='get_data',
    provide_context=True,
    python_callable=get_data,
    dag=dag,
)



stop_op = DummyOperator(task_id='stop_task', dag=dag)


get_data_step >> stop_op
