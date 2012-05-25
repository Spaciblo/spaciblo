from django.conf import settings
from django.test.client import Client
from django.contrib.auth.models import User
from django.test import TestCase, TransactionTestCase

from blank_slate.wind.events import EventHandler

from spaciblo.sim.sim_client import SimClient
from spaciblo.sim.events import TemplateUpdated
from spaciblo.sim.models import Space, SpaceMember
from spaciblo.sim.sim_server import SimulationServer
from spaciblo.sim.management.commands.load_example_spaces import Command

class SimTest(TransactionTestCase): 
	"""A test suite for the sim server and client.
	It must be a TransactionalTestCase because we're accessing the db in multiple threads."""
	
	fixtures = ['auth.json', 'sites.json']
	
	def setUp(self):
		self.command = Command()
		self.command.handle_noargs()
		self.space1 = Space.objects.all()[0]
		self.space1.state = 'admin_only'
		self.space1.save()

		self.client = Client()
		self.client2 = Client()
		self.sim_server = SimulationServer()
		self.sim_server.start()
		self.user1 = User.objects.get(username='trevor')
		self.user2 = User.objects.get(username='sarah')

	def tearDown(self):
		self.sim_server.stop()

	def test_sim_setup(self):
		self.client.login(username=self.user1.username, password='1234')
		self.client2.login(username=self.user2.username, password='1234')

		event_handler = EventHandler()

		sim_client = SimClient(self.user1.session_key, '127.0.0.1', self.sim_server.wind_server.ws_server.port, '127.0.0.1:8000', event_handler=event_handler.handle_event)

		sim_client.authenticate()
		event = event_handler.events.get(True, 10)
		self.failUnless(event.authenticated)
		self.failUnlessEqual(self.user1.username, event.username)
		self.failUnlessEqual(self.user1.username, sim_client.username)

		# TODO test the space info fetching
		#sim_client.request_pool_info()
		#event = event_handler.events.get(True, 10)
		#self.failUnless(event.infos)
		#self.failUnless(event.infos['space_infos'])
		#self.failUnless(event.infos['space_infos'][0].has_key('name'))
		#self.failUnless(event.infos['space_infos'][0].has_key('url'))

		space = self.space1
		sim_client.join_space(space.id)
		event = event_handler.events.get(True, 10)
		self.failUnless(event.joined)
		self.failUnlessEqual(space.id, sim_client.space_id)

		sim_client.add_user()
		event = event_handler.events.get(True, 10)
		self.failUnless(sim_client.is_member)
		self.failUnless(sim_client.is_editor)
		self.failUnless(sim_client.is_admin)
		self.failUnless(sim_client.scene)
		self.failUnless(len(sim_client.scene.children) > 0)
		event = event_handler.events.get(True, 10)
		self.failUnlessEqual(event.username, self.user1.username)
			
		event_handler2 = EventHandler()
		sim_client2 = SimClient(self.user2.session_key, '127.0.0.1', self.sim_server.wind_server.ws_server.port, '127.0.0.1:8000', event_handler=event_handler2.handle_event)
		sim_client2.authenticate()
		event = event_handler2.events.get(True, 10)
		self.failUnless(event.authenticated)

		space.remove_member(self.user2)
		sim_client2.join_space(space.id)
		event = event_handler2.events.get(True, 10)
		self.failUnless(event.joined == False, event.to_json()) # client 2 is not a member yet
		space_member = space.add_member(self.user2)
		sim_client2.join_space(space.id)
		event = event_handler2.events.get(True, 10)
		self.failUnless(event.joined == False, event.to_json())

		space_member.is_admin = True
		space_member.save()
		sim_client2.join_space(space.id)
		event = event_handler2.events.get(True, 10)
		self.failUnless(event.joined)
		
		sim_client2.add_user()
		event = event_handler2.events.get(True, 10)
		self.failUnless(event.joined)
		self.failUnless(event.is_member)
		event_handler2.events.get(True, 10) # ignore the UserAdded event
		event = event_handler.events.get(True, 10)
		self.failUnless(event.parent_id)
		event = event_handler.events.get(True, 10)
		self.failUnlessEqual(event.username, self.user2.username)
		
		event_handler.events.get(True, 10) # ignore the NodeAdded event
		sim_client.notify_template_updated(3, '/url')
		event = event_handler.events.get(True, 10)
		self.failUnlessEqual(event.template_id, 3)
		event_handler2.events.get(True, 10) # ignore the NodeAdded event
		event = event_handler2.events.get(True, 10)
		self.failUnlessEqual(event.template_id, 3)

		sim_client.notify_template_updated(2, '/some/thing/2', 'moon')
		event = event_handler.events.get(True, 10)
		self.failUnlessEqual(event.template_id, 2)
		self.failUnlessEqual(event.key, 'moon')
		self.failUnlessEqual(event.url, '/some/thing/2')
		event = event_handler2.events.get(True, 10)
		self.failUnlessEqual(event.template_id, 2)
		self.failUnlessEqual(event.key, 'moon')

		sim_client.close()
		sim_client2.close()
		
# Copyright 2010,2011,2012 Trevor F. Smith (http://trevor.smith.name/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
