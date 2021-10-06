# -*- coding: utf-8 -*-
from airflow import DAG
from airflow.operators.twitter_api import TwitterOperator
from airflow.operators.xpath_evaluation_operator import XPathEvaluationOperator
from airflow.utils.dates import days_ago

default_args = {
    'owner': 'airflow_admin',
    'depends_on_past': False
}

dag = DAG(
    dag_id='twitter_hashtag_search_COVID19',
    start_date=days_ago(1),
    schedule_interval='@once',
    default_args=default_args,
    catchup=False
)

twitter_changelog_version_check = XPathEvaluationOperator(
    task_id='twitter_changelog_version_check',
    dag=dag,
    evaluated_url='https://developer.twitter.com/en/docs/twitter-ads-api/versioning',
    xpath='//*[@id="twtr-main"]/div/div/div[2]/div/div[5]/div/div/div/div/div[2]/div[4]/div[2]/div/div/p'
)

twitter_hashtag_search_COVID19 = TwitterOperator(
    task_id='twitter_hashtag_search_COVID19',
    dag=dag,
    method='search',
    response_limit=1000,
    extra_args={'q': '#COVID19', 'count': 100},
    twitter_conn_id='twitter_default',
    path='/tmp',
    partition_cols=['created_at_year', 'created_at_month', 'created_at_day']
)

twitter_changelog_version_check >> twitter_hashtag_search_COVID19

if __name__ == "__main__":
    dag.cli()
