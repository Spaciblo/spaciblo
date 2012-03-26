"""Simulations and a simple pool."""
import Queue
import datetime
import threading
import simplejson
from time import sleep

from django.conf import settings

from blank_slate.wind.client import Client
from blank_slate.wind.events import Heartbeat, CreateChannelRequest, SubscribeRequest, SubscribeResponse
from blank_slate.wind.handler import to_json, from_json

from spaciblo.sim.events import SpaceChannel, NodeAdded, NodeRemoved, PlaceableMoved
from spaciblo.sim.models import Space
from spaciblo.sim.glge import Scene, Object, Group

DEFAULT_SIM_POOL = None

class Simulator:
	"""The class responsible for managing various aspects of Space simulation such as the event queue, run loop, and scene."""
	initializing, ready, running, terminating, stopped = range(5)
	possible_states = [ initializing, ready, running, terminating, stopped ]
	
	def __init__(self, pool, space):
		self.state = Simulator.initializing
		self.should_run = False

		self.pool = pool
		self.space = space
		self.scene = Scene().populate(simplejson.loads(space.scene_document))
		
		self.event_queue = Queue.Queue(-1)
		self.script_engine = None
		self.physics_engine = None
		
		self.state = Simulator.ready

		self.client = Client(settings.WEB_SOCKETS_SECRET, '127.0.0.1', settings.WEB_SOCKETS_PORT, '127.0.0.1:8000', self.handle_event)
		self.client.authenticate()

	@property
	def channel_id(self): return SpaceChannel.generate_channel_id(self.space.id)

	def handle_event(self, event): self.event_queue.put(event)

	def __unicode__(self): return "Simulator for %s" % self.space

	def stop(self):
		if self.state != Simulator.running:
			print 'Tried to stop a simulator which is not running: ' % self.state
			return
		self.client.close()
		self.state = Simulator.terminating
		self.should_run = False

	def run(self):
		"""The simulation loop"""
		if not self.state == Simulator.ready:
			print "Tried to run a simulator in an unready state: %s" % self
			return
		self.state = Simulator.running
		self.should_run = True
		while self.should_run:
			try:
				event = self.event_queue.get(block=True, timeout=5)
			except Queue.Empty:
				self.client.send_event(Heartbeat())
				continue
			
			if not self.should_run:
				self.state = Simulator.stopped
				return
			
			if event.event_name() == 'UserAdded':
				user_node = self.scene.get_user(event.username)
				if user_node is None:
					user_node = Group()
					user_node.username = event.username
					user_node.set_loc(event.position)
					user_node.set_quat(event.orientation)
					self.scene.children.append(user_node)
					self.client.send_event(NodeAdded(self.scene.uid, to_json(user_node)))
				else:
					print "Already have a user with id", event.username

			elif event.event_name() == 'NodeAdded':
				pass

			elif event.event_name() == 'UserExited':
				#print 'User exited', event.username
				user_node = self.scene.get_user(event.username)
				if user_node:
					self.scene.remove_node(user_node.uid)
					self.client.send_event(NodeRemoved(user_node.uid))

			elif event.event_name() == 'UserMoveRequest':
				if event.connection.user != None and event.username == event.connection.user.username:
					user_node = self.scene.get_user(event.username)
					if user_node == None:
						print "No such user node: %s" % event.username
					else:
						user_node.set_loc(event.position)
						user_node.set_quat(event.orientation)
						response = PlaceableMoved(user_node.uid, user_node.loc, user_node.quat)
						self.client.send_event(response)

			elif event.event_name() == 'TemplateUpdated':
				pass

			elif event.event_name() == 'AuthenticationResponse':
				self.client.send_event(CreateChannelRequest(self.channel_id, class_name='spaciblo.sim.events.SpaceChannel', options={'space_id': self.space.id}))

			elif event.event_name() == 'ChannelCreated' or event.event_name() == 'ChannelExists':
				self.client.send_event(SubscribeRequest(self.channel_id))

			elif event.event_name() == 'SubscribeResponse':
				pass

			else:
				print "Unknown event in simulator: %s" % event.event_name()

		self.state = Simulator.stopped

class SimulationThread(threading.Thread):
	def __init__ (self, pool, space):
		self.pool = pool
		self.space = space
		threading.Thread.__init__ ( self )

	def run(self):
		self.sim = Simulator(self.pool, self.space)
		self.pool.add_simulator(self.sim)
		try:
			self.sim.run()
		finally:
			self.pool.remove_simulator(self.sim)

class SimulatorPool:
	"""A simple manager for space simulators."""
	initializing, running, terminating, stopped = range(4)
	possible_states = [initializing, running, terminating, stopped]

	def __init__(self, sim_server):
		self.state = SimulatorPool.initializing
		self.sim_server = sim_server
		self.simulators= [] #<time_since_populated>
		self.state = SimulatorPool.running
	
	def get_simulator(self, space_id):
		for sim in self.simulators:
			if sim.space.id == space_id: return sim
		return None
	
	def add_simulator(self, simulator):
		self.simulators.append(simulator)

	def remove_simulator(self, simulator):
		self.simulators.remove(simulator)

	def start_all_spaces(self):
		for space in Space.objects.all():
			sim_thread = SimulationThread(self, space)
			sim_thread.start()

	def stop_all_spaces(self):
		self.state = SimulatorPool.terminating
		for sim in self.simulators:
			sim.stop()
		self.state = SimulatorPool.stopped

	def __unicode__(self):
		return "Simulator Pool"

	def stateToString(self, state=None):
		if not state: state = self.state
		if state == 0: return 'initializing'
		if state == 1: return 'running'
		if state == 2: return 'terminating'
		if state == 3: return 'stopped'

# Copyright 2010 Trevor F. Smith (http://trevor.smith.name/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
