import time
import pprint
import simplejson
import datetime

from django.test import TestCase, TransactionTestCase
from django.test.client import Client
from django.contrib.auth.models import User
from django.core import mail
from django.test.client import Client

from blank_slate.wind.handler import to_json, from_json

from spaciblo.sim.glge import Scene
from spaciblo.sim.loaders.primitives import create_plane, create_box

class SceneTest(TransactionTestCase): 
	"""A test suite for the glge scene"""

	def setUp(self):
		self.scene = Scene()
		self.scene.locX = 10
		self.scene.locY = -20
		self.scene.children.append(create_plane())
		self.scene.children.append(create_box())
		self.scene.backgroundColor = [0.5, 0, 0.23]
		self.scene_json = to_json(self.scene)
		self.parsed_json = simplejson.loads(self.scene_json)

	def tearDown(self):
		pass

	def test_serialization(self):
		self.assertEqual(self.parsed_json['backgroundColor'], self.scene.backgroundColor)
		self.assertEqual(len(self.parsed_json['children']), 2)
		self.assertEqual(self.parsed_json['children'][0]['mesh']['faces'], range(6))
		self.assertEqual(self.parsed_json['locX'], self.scene.locX)
		
		scene2 = Scene().populate(self.parsed_json)
		self.assertEqual(scene2.backgroundColor, self.scene.backgroundColor)
		self.assertEqual(len(scene2.children), len(self.scene.children))
		self.assertEqual(scene2.locX, self.scene.locX)
		self.assertEqual(scene2.uid, self.scene.uid)
		self.assertEqual(scene2.children[0].uid, self.scene.children[0].uid)
		
# Copyright 2010 Trevor F. Smith (http://trevor.smith.name/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
