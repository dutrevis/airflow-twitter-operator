from airflow.plugins_manager import AirflowPlugin
from version_check.links.changelog_url import ChangelogUrlLink
from version_check.operators.version_check_operator import VersionCheckOperator


class AirflowVersionCheckOperatorPlugin(AirflowPlugin):
    name = "version_check_operator"
    operators = [VersionCheckOperator]
    sensors = []
    hooks = []
    executors = []
    macros = []
    admin_views = []
    flask_blueprints = []
    menu_links = []
    appbuilder_views = []
    appbuilder_menu_items = []
    global_operator_extra_links = []
    operator_extra_links = [ChangelogUrlLink(), ]
