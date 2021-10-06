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
    :param xpath: The XPath string used to retrieve HTML elements from the evaluated URL.
    :type xpath: str
    :param evaluated_url: The URL of the website where the XPath will be applied to retrieve
        an element that will be evaluated.
    :type evaluated_url: str
    :param evaluated_value: String or Datetime object to be used as the expected value for
        evaluation. When ``None`` value is provided, falls back to ``datetime.now()``.
    :type evaluated_value: str or datetime
    :param fail_on_not_found: defines the behavior for when XPath returns no elements.
        Default is ``True``.
    :type fail_on_not_found: boolean
    :param max_datetime_diff_sec: maximum value of seconds that a datetime difference
        evaluation may reach before failing the task. Default is ``0``.
    :type max_datetime_diff_sec: int
    :param warn_datetime_diff_sec: maximum value of seconds that a datetime difference
        evaluation may reach before executing the warning callback. Default is ``24*3600``.
    :type warn_datetime_diff_sec: int
    :param on_warning_callback: function to be executed when ``warn_datetime_diff_sec`` is
        equal or higher than the evaluated datetime difference. Receives the ``context`` arg.
        Default is ``None``.
    :type on_warning_callback: callable
    """

    template_fields = ['xpath', 'evaluated_url', 'evaluated_value']

    ui_color = '#19647e'

    operator_extra_links = (
        EvaluatedUrlLink(),
    )

    def __init__(self,
                 xpath,
                 evaluated_url,
                 evaluated_value: str or datetime = None,
                 fail_on_not_found: bool = True,
                 max_datetime_diff_sec: int = 0,
                 warn_datetime_diff_sec: int = 24*3600,
                 on_warning_callback: callable = None,
                 *args, **kwargs):
        kwargs["python_callable"] = self._evaluate_xpath
        kwargs["provide_context"] = True
        super().__init__(*args, **kwargs)
        self.xpath = xpath
        self.evaluated_url = evaluated_url
        self.evaluated_value = evaluated_value or datetime.now()
        self.fail_on_not_found = fail_on_not_found
        self.max_datetime_diff_sec = max_datetime_diff_sec
        self.warn_datetime_diff_sec = warn_datetime_diff_sec
        self.on_warning_callback = on_warning_callback

    def _evaluate_xpath(self, **kwargs):
        kwargs["ti"].xcom_push(key="evaluated_url",
                               value=self.evaluated_url)

        xpath_list = self._xpath_from_url(self.evaluated_url, self.xpath)

        if not xpath_list:
            not_found_log = f"No elements found with provided XPath in '{self.evaluated_url}'"

            if self.fail_on_not_found:
                raise Exception(not_found_log)

            self.log.warn(not_found_log)
            return True

        actual_value = self._first_string_from_xpath_list(xpath_list)
        self.log.info(
            f"Using first object found '{actual_value}' as actual value...")

        if isinstance(self.evaluated_value, str):
            return actual_value == self.evaluated_value

        if isinstance(self.evaluated_value, datetime):
            self.log.info(
                f"Parsing actual value '{actual_value}' as datetime...")

            parsed_datetime = parser.parse(actual_value)

            datetime_diff_sec = (parsed_datetime -
                                 self.evaluated_value).total_seconds()
            if datetime_diff_sec <= self.warn_datetime_diff_sec:
                self.log.warn(
                    "Diff seconds is of {}. Executing warning callback...".format(
                        datetime_diff_sec
                    )
                )
                self.on_warning_callback(kwargs)

            return datetime_diff_sec > self.max_datetime_diff_sec

        raise ValueError(
            f"Evaluated value '{self.evaluated_value}' must be a string or a datetime object.")

    def _xpath_from_url(self, url, xpath):
        self.log.info(f"Searching '{url}' for objects in the given XPath...")

        response = requests.get(url)
        tree = html.fromstring(response.content)
        xpath_list = tree.xpath(xpath)

        self.log.info(f"Found {len(xpath_list)} objects")

        return xpath_list

    @staticmethod
    def _first_string_from_xpath_list(xpath_list):
        extracted_element = xpath_list[0]
        actual_value = (extracted_element.text
                        if type(extracted_element) == html.HtmlElement
                        else extracted_element)

        return actual_value
