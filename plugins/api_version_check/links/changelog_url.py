from airflow.models.baseoperator import BaseOperatorLink
from airflow.models import TaskInstance


class ChangelogUrlLink(BaseOperatorLink):
    name = 'Changelog URL'

    def get_link(self, operator, dttm):
        ti = TaskInstance(task=operator, execution_date=dttm)
        changelog_url = ti.xcom_pull(
            task_ids=operator.task_id,
            key="changelog_url"
        )
        return changelog_url
