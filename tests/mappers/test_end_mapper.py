# -*- coding: utf-8 -*-
# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for the End mapper."""
import ast
import unittest
from unittest import mock
from xml.etree.ElementTree import Element

from o2a.converter.parsed_action_node import ParsedActionNode
from o2a.converter.task import Task
from o2a.converter.workflow import Workflow
from o2a.converter.relation import Relation
from o2a.mappers import end_mapper
from o2a.mappers.base_mapper import BaseMapper
from o2a.mappers.decision_mapper import DecisionMapper


class TestEndMapper(unittest.TestCase):
    oozie_node = Element("end")

    def test_create_mapper(self):
        mapper = self._get_end_mapper()
        # make sure everything is getting initialized correctly
        self.assertEqual("test_id", mapper.name)

    def test_convert_tasks_and_relations(self):
        mapper = self._get_end_mapper()
        tasks, relations = mapper.to_tasks_and_relations()
        self.assertEqual([Task(task_id="test_id", template_name="dummy.tpl")], tasks)
        self.assertEqual([], relations)

    def test_required_imports(self):
        mapper = self._get_end_mapper()
        imps = mapper.required_imports()
        imp_str = "\n".join(imps)
        ast.parse(imp_str)

    def test_on_parse_finish_simple_should_remove_end_node(self):
        workflow = Workflow(input_directory_path="", output_directory_path="", dag_name="DAG_NAME_B")

        mapper = self._get_end_mapper("second_task")

        workflow.nodes["first_task"] = ParsedActionNode(mock.Mock(autospec=BaseMapper))
        workflow.nodes["second_task"] = ParsedActionNode(mapper)

        workflow.relations = {Relation(from_task_id="first_task", to_task_id="second_task")}

        mapper.on_parse_finish(workflow)

        self.assertEqual({"first_task"}, set(workflow.nodes.keys()))
        self.assertEqual(set(), workflow.relations)

    def test_on_parse_finish_decision_should_not_remove_end_node(self):
        workflow = Workflow(input_directory_path="", output_directory_path="", dag_name="DAG_NAME_B")

        mapper = self._get_end_mapper("end_task")

        workflow.nodes["first_task"] = ParsedActionNode(
            mock.Mock(spec=DecisionMapper), tasks=[self._get_dummy_task("first_task")]
        )
        workflow.nodes["second_task"] = ParsedActionNode(
            mock.Mock(spec=BaseMapper), tasks=[self._get_dummy_task("second_task")]
        )
        workflow.nodes["end_task"] = ParsedActionNode(mapper, tasks=[self._get_dummy_task("end_task")])

        workflow.relations = {
            Relation(from_task_id="first_task", to_task_id="end_task"),
            Relation(from_task_id="second_task", to_task_id="end_task"),
        }

        mapper.on_parse_finish(workflow)

        self.assertEqual({"first_task", "second_task", "end_task"}, set(workflow.nodes.keys()))
        self.assertEqual({Relation(from_task_id="first_task", to_task_id="end_task")}, workflow.relations)

    def _get_end_mapper(self, name="test_id"):
        mapper = end_mapper.EndMapper(oozie_node=self.oozie_node, name=name, dag_name="DAG_NAME_B")
        return mapper

    @staticmethod
    def _get_dummy_task(task_id):
        return Task(task_id=task_id, template_name="dummy.tpl")
