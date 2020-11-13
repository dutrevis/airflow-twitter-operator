from airflow.hooks.base_hook import BaseHook
from tweepy import auth, API, Cursor
import tweepy


class TwitterHook(BaseHook):
    def __init__(
            self,
            conn_id='twitter_default',
            *args,
            **kwargs):

        # Twitter custom connection
        self.conn_id = conn_id
        self.connection = self.get_connection(self.conn_id)
        conn_extra = self.connection.extra_dejson

        self.consumer_key = conn_extra['twitter_api_key']
        self.consumer_secret = conn_extra['twitter_api_secret_key']
        self.access_token = conn_extra.get('twitter_access_token')
        self.access_token_secret = conn_extra.get('twitter_access_token_secret')
        self.verifier = conn_extra.get('twitter_verifier')
        self.redirect_url = None

        self.auth = auth.OAuthHandler(
            self.consumer_key,
            self.consumer_secret
        )
        
        # [BEGIN: First authentication process]
        # See http://docs.tweepy.org/en/latest/auth_tutorial.html
        if not self.access_token or not self.access_token_secret:
            if not self.verifier:
                self.redirect_url = self.auth.get_authorization_url()
                raise tweepy.TweepError(f"Access tokens required for authentication.\n"
                                        f"Proceed to '{self.redirect_url}', authorize the application "
                                        f"and add the “verifier” number, that Twitter will supply, into "
                                        f"'{conn_id}' Twitter connection.")
            # [BEGIN: First authentication with verifier number]
            else:
                from airflow.settings import Session

                self.auth.request_token['oauth_token_secret'] = self.verifier
            
                self.auth.get_access_token(self.verifier)
                self.access_token = self.auth.access_token
                self.access_token_secret = self.auth.access_token_secret
                
                conn_extra['twitter_access_token'] = self.access_token
                conn_extra['twitter_access_token_secret'] = self.access_token_secret
                self.connection.set_extra(conn_extra)
                              
                session = Session()
                session.add(self.connection)
                session.commit()

                self.log.info(f'Connection {self.conn_id} updated with "twitter_access_token"'
                              f'and "twitter_access_token_secret" values.')
            # [END: First authentication with verifier number]
        # [END: First authentication process]

        self.auth.set_access_token(self.access_token, self.access_token_secret)

    def run(self,
            method,
            response_limit=0,
            extra_args={}):

        api = API(
            self.auth,
            wait_on_rate_limit=True,
            wait_on_rate_limit_notify=True
        )

        response_data = []

        for t in Cursor(getattr(api, method), **extra_args).items(response_limit):
            response_data.append(t._json)
        
        return response_data
