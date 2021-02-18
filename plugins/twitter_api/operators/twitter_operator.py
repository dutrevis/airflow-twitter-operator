from datetime import datetime

import pandas as pd
from airflow.models.baseoperator import BaseOperator
from airflow.utils.decorators import apply_defaults
from twitter_api.hooks.twitter_hook import TwitterHook
from twitter_api.links.authorization_url import AuthorizationUrlLink


class TwitterOperator(BaseOperator):

    operator_extra_links = (
        AuthorizationUrlLink(),
    )

    @apply_defaults
    def __init__(self,
                method,
                response_limit=0,
                extra_args={},
                twitter_conn_id='twitter_default',
                path='/tmp',
                partition_cols=[],
                *args, **kwargs):
        '''
        Execute a request on a given twitter API and saves parquet files
        partitioned by a given list of columns potentially returned.
        http://docs.tweepy.org/en/latest/api.html
        '''
        super(TwitterOperator, self).__init__(*args, **kwargs)
        self.method = method
        self.response_limit = response_limit
        self.extra_args = extra_args
        self.twitter_conn_id = twitter_conn_id
        self.path = f'{path}/{method}'
        self.partition_cols = partition_cols

    def execute(self, context):
        
        twitter_hook = TwitterHook(conn_id = self.twitter_conn_id)
        context["ti"].xcom_push(key="authorization_url", value=twitter_hook.authorization_url)

        response_data = twitter_hook.run(
            self.method,
            response_limit=self.response_limit,
            extra_args=self.extra_args)

        if response_data:
            df = pd.DataFrame(response_data)

            extracted_at = datetime.now()
            df['extracted_at'] = extracted_at.strftime('%Y-%m-%d %H:%M:%S')
            df['extracted_at_year'] = extracted_at.year
            df['extracted_at_month'] = extracted_at.month
            df['extracted_at_day'] = extracted_at.day
            df['extracted_at_time'] = extracted_at.time().strftime('%H:%M:%S')

            if 'created_at' in list(df.keys()):
                df['created_at'] = pd.to_datetime(df['created_at'], format='%a %b %d %H:%M:%S %z %Y')
                df['created_at_year'] = pd.DatetimeIndex(df['created_at']).year
                df['created_at_month'] = pd.DatetimeIndex(df['created_at']).month
                df['created_at_day'] = pd.DatetimeIndex(df['created_at']).day
                df['created_at_time'] = pd.DatetimeIndex(df['created_at']).strftime('%H:%M:%S')

            for c in self.partition_cols:
                if not c in df.columns:
                    raise KeyError(f"Partition column {c} is not"
                                   f" present in response data.")

            df = self._assure_column_types(df)

            df.to_parquet(
                fname=self.path,
                index=False,
                partition_cols=self.partition_cols
            )

    def _assure_column_types(self, df):
        '''
        Assures column type according to its content
        See https://github.com/pandas-dev/pandas/issues/21228
        '''

        for col in df.columns:
            weird = (df[[col]].applymap(type) !=
                    df[[col]].iloc[0].apply(type)).any(axis=1)
            if len(df[weird]) > 0:
                df[col] = df[col].astype(str)
            if df[col].dtype == list:
                df[col] = df[col].astype(str)

        return df
