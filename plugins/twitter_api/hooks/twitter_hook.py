from airflow.hooks.base_hook import BaseHook
from tweepy import auth, API, Cursor, TweepError


class TwitterHook(BaseHook):
    def __init__(
            self,
            conn_id='twitter_default',
            *args,
            **kwargs):

        # Twitter custom connection
        self.conn_id = conn_id
        self.connection = self.get_connection(self.conn_id)
        self.authorization_url = None

        self.__authentication()

    def run(self,
            method,
            response_limit=0,
            extra_args={}):

        if self.authorization_url:
            raise TweepError(f"Access tokens required for authentication.\n"
                            f"Proceed to {self.authorization_url} to authorize the application "
                            f"and add the Twitter supplied “verifier” number "
                            f"into '{self.conn_id}' Twitter connection.")

        api = API(
            self.auth,
            wait_on_rate_limit=True,
            wait_on_rate_limit_notify=True
        )

        response_data = []

        for t in Cursor(getattr(api, method), **extra_args).items(response_limit):
            response_data.append(t._json)
        
        return response_data

    def __authentication(self):
        # See http://docs.tweepy.org/en/latest/auth_tutorial.html

        conn_extra = self.connection.extra_dejson

        consumer_key = conn_extra['twitter_api_key']
        consumer_secret = conn_extra['twitter_api_secret_key']
        access_token = conn_extra.get('twitter_access_token')
        access_token_secret = conn_extra.get('twitter_access_token_secret')
        verifier = conn_extra.get('twitter_verifier')
        
        self.auth = auth.OAuthHandler(consumer_key, consumer_secret)

        # [BEGIN: First authentication process]
        if not access_token or not access_token_secret:
            if not verifier:
                self.authorization_url = self.auth.get_authorization_url()
            # [BEGIN: First authentication with verifier number]
            else:
                self.auth.request_token['oauth_token_secret'] = verifier
                self.auth.get_access_token(verifier)

                self.__update_conn_extra_tokens(self.auth, self.connection)
            # [END: First authentication with verifier number]
        # [END: First authentication process]

        else:
            self.auth.set_access_token(access_token, access_token_secret)

    def __update_conn_extra_tokens(self, auth, connection):
        from airflow.settings import Session

        conn_extra = connection.extra_dejson

        conn_extra['twitter_access_token'] = auth.access_token
        conn_extra['twitter_access_token_secret'] = auth.access_token_secret
        connection.set_extra(conn_extra)

        session = Session()
        session.add(connection)
        session.commit()

        self.log.info(f'Connection {connection.conn_id} updated with "twitter_access_token"'
                      f'and "twitter_access_token_secret" values.')
