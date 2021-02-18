# References
# :- https://airflow.apache.org/docs/stable/plugins.html
# :- https://pybit.es/introduction-airflow.html
# :- hhttps://github.com/vjgpt/twitter-pipeline
# :- https://medium.com/@junjiejiang94/airflow-with-twitter-scraper-google-cloud-storage-big-query-tweets-relating-to-covid19-f43b8930ab74

from airflow.plugins_manager import AirflowPlugin
from twitter_api.hooks.twitter_hook import TwitterHook
from twitter_api.operators.twitter_operator import TwitterOperator
from twitter_api.links.authorization_url import AuthorizationUrlLink


class AirflowTwitterApiPlugin(AirflowPlugin):
    name = "twitter_api"
    operators = [TwitterOperator]
    sensors = []
    hooks = [TwitterHook]
    executors = []
    macros = []
    admin_views = []
    flask_blueprints = []
    menu_links = []
    appbuilder_views = []
    appbuilder_menu_items = []
    global_operator_extra_links = []
    operator_extra_links = [AuthorizationUrlLink(),]
