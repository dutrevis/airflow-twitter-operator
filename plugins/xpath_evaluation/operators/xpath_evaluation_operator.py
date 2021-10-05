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
from dateutil import parser

import requests
from lxml import html
from airflow.operators.python_operator import ShortCircuitOperator

from xpath_evaluation.links.evaluated_url import EvaluatedUrlLink


class XPathEvaluationOperator(ShortCircuitOperator):
    """
    Waits for a different DAG or a task in a different DAG to complete for a
    specific execution_date

    :param evaluated_url: The dag_id that contains the task you want to
    :type evaluated_url: str
    :param xpath: The task_id that contains the task you want to
        wait for. 
    :type xpath: str or None
    :param version: Iterable of allowed states, default is ``['success']``
        If ``None`` (default value) the operator falls waits for the DAG
    :type version: Iterable
    :param warning_message_days: Iterable of failed or dis-allowed states, default is ``1``
    :type warning_message_days: int
    """

    template_fields = ['evaluated_url', 'xpath']

    ui_color = '#19647e'

    operator_extra_links = (
        EvaluatedUrlLink(),
    )

    MAX_DEPRECATION_DIFF_SEC = 3600

    def __init__(self,
                 evaluated_url,
                 xpath,
                 version=None,
                 warning_message_days: int = 1,
                 soft_fail_on_evaluation: bool = False,
                 soft_fail_on_not_found: bool = True,
                 *args, **kwargs):
        kwargs["python_callable"] = self._python_callable
        kwargs["provide_context"] = True
        kwargs["soft_fail"] = True
        super().__init__(*args, **kwargs)
        self.evaluated_url = evaluated_url
        self.xpath = xpath
        self.version = version
        self.warning_message_days = warning_message_days

    def _python_callable(self, **kwargs):
        kwargs["ti"].xcom_push(key="evaluated_url",
                               value=self.evaluated_url)

        xpath_list = self._xpath_from_url(self.evaluated_url, self.xpath)
        extracted_str = self._first_string_from_xpath_list(xpath_list)
        self.log.info(
            f"Using first object found '{extracted_str}' as actual value...")

        if self.version:
            self.log.info(
                f"Evaluating actual value over the provided expected version '{self.version}'...")
            return extracted_str == self.version
        self.log.warn(
            "No expected version provided. Evaluating actual value over the current datetime...")

        time_until_deprecation = self._time_diff_from_string(extracted_str)
        if time_until_deprecation.days <= self.warning_message_days:
            self._on_failure_callback(kwargs, log_level="WARN")
        return time_until_deprecation.total_seconds() > self.MAX_DEPRECATION_DIFF_SEC

    def _xpath_from_url(self, url, xpath):
        self.log.info(f"Searching '{url}' for objects in the given XPath...")
        response = requests.get(url)
        tree = html.fromstring(response.content)
        xpath_list = tree.xpath(xpath)
        if not xpath_list:
            raise ValueError(f"XPath '{xpath}' not found in '{url}'")
        self.log.info(f"Found {len(xpath_list)} objects")
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
