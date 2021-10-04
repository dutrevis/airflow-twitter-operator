#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

from datetime import datetime
from typing import Any, Callable, FrozenSet, Iterable, Optional, Union

import requests
from airflow.sensors.base_sensor_operator import BaseSensorOperator
from airflow.operators.python_operator import ShortCircuitOperator
from dateutil import parser
from lxml import html

from version_check.links.changelog_url import ChangelogUrlLink


class VersionCheckOperator(ShortCircuitOperator):
    """
    Waits for a different DAG or a task in a different DAG to complete for a
    specific execution_date

    :param changelog_url: The dag_id that contains the task you want to
    :type changelog_url: str
    :param xpath: The task_id that contains the task you want to
        wait for. 
    :type xpath: str or None
    :param version: Iterable of allowed states, default is ``['success']``
        If ``None`` (default value) the operator falls waits for the DAG
    :type version: Iterable
    :param warning_message_days: Iterable of failed or dis-allowed states, default is ``1``
    :type warning_message_days: int
    """

    template_fields = ['changelog_url', 'xpath']

    ui_color = '#19647e'

    operator_extra_links = (
        ChangelogUrlLink(),
    )

    MAX_DEPRECATION_DIFF_SEC = 3600

    def __init__(self,
                 changelog_url,
                 xpath,
                 version=None,
                 warning_message_days: int = 1,
                 *args, **kwargs):
        kwargs["python_callable"] = self._python_callable
        kwargs["provide_context"] = True
        super().__init__(*args, **kwargs)
        self.changelog_url = changelog_url
        self.xpath = xpath
        self.version = version
        self.warning_message_days = warning_message_days

    def _python_callable(self, **kwargs):
        kwargs["ti"].xcom_push(key="changelog_url",
                               value=self.changelog_url)

        self.log.info(
            f"Searching '{self.changelog_url}' for objects in the given XPath...")
        xpath_list = self._xpath_from_url(self.changelog_url, self.xpath)
        self.log.info(f"Found {len(xpath_list)} objects")

        extracted_str = self._first_string_from_xpath_list(xpath_list)
        self.log.info(
            f"Using first object found '{extracted_str}' as actual value...")

        if self.version:
            self.log.info(
                f"Validating actual value over the provided expected version '{self.version}'...")
            return extracted_str == self.version
        self.log.warn(
            "No expected version provided. Validating actual value over the current datetime...")

        time_until_deprecation = self._time_diff_from_string(extracted_str)
        if time_until_deprecation.days <= self.warning_message_days:
            self._on_failure_callback(kwargs, log_level="WARN")
        return time_until_deprecation.total_seconds() > self.MAX_DEPRECATION_DIFF_SEC

    @staticmethod
    def _xpath_from_url(url, xpath):
        response = requests.get(url)
        tree = html.fromstring(response.content)
        xpath_list = tree.xpath(xpath)
        if not xpath_list:
            raise ValueError(f"XPath '{xpath}' not found in '{url}'")
        return xpath_list

    @staticmethod
    def _first_string_from_xpath_list(xpath_list):
        if not xpath_list:
            raise TypeError(f"Argument 'xpath_list' must be a non-empty list")
        extracted_element = xpath_list[0]
        extracted_str = (extracted_element.text
                         if type(extracted_element) == html.HtmlElement
                         else extracted_element)
        return extracted_str

    @staticmethod
    def _time_diff_from_string(datetime_string):
        parsed_datetime = parser.parse(datetime_string)
        current_datetime = datetime.now()
        return parsed_datetime - current_datetime

    def _on_failure_callback(self, context, log_level="ERROR"):
        print("error")
