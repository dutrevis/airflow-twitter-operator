from airflow.models.baseoperator import BaseOperatorLink
from airflow.models import TaskInstance

class AuthorizationUrlLink(BaseOperatorLink):
    name = 'Authorization URL'

    def get_link(self, operator, dttm):
        ti = TaskInstance(task=operator, execution_date=dttm)
        authorization_url = ti.xcom_pull(
            task_ids=operator.task_id,
            key="authorization_url"
        )
        return authorization_url
