import sys
import time, datetime
import pprint, traceback
import Queue
import threading
import simplejson

from django.conf import settings
from django.contrib.auth import SESSION_KEY, BACKEND_SESSION_KEY, load_backend
from django.contrib.auth.models import AnonymousUser

from blank_slate.wind.events import parse_event_json
from blank_slate.wind.server import Server as WindServer
from blank_slate.wind.handler import to_json

import spaciblo.sim
import spaciblo.sim.sim_pool as sim_pool
import spaciblo.sim.events as events
from spaciblo.sim.models import Space, SimulatorPoolRegistration

class WebSocketConnection:
	"""Maintains state and an outgoing event queue for a WebSockets connection"""
	def __init__(self, client_socket, server):
		self.client_socket = client_socket
		self.server = server
		self.user = None
		self.space_id = None
		self.disconnected = False
		
		self.outgoing_events = Queue.Queue(-1)
		self.outgoing_event_thread = threading.Thread(target=self.handle_outgoing)
		self.outgoing_event_thread.setDaemon(True)
		self.outgoing_event_thread.start()

	def handle_outgoing(self):
		"""A loop which handles outgoing events.  Does not return until the connection closes."""
		while not self.disconnected:
			try:
				event = self.outgoing_events.get(block=True, timeout=5)
			except Queue.Empty:
				continue
			try:
				self.client_socket.send('\x00')
				self.client_socket.send(event.to_json())
				self.client_socket.send('\xff')
			except IOError:
				#traceback.print_exc()
				pass
		
	def handle_incoming(self):
		"""A loop which handles incoming messages.  Does not return until the connection closes."""
		while not self.disconnected:
			incoming_data = receive_web_socket_message(self.client_socket)
			if incoming_data == None: 
				break
			#print 'Incoming:', incoming_data
			event = parse_event_json(incoming_data)
			if not event:
				print "Could not read an event from the data: %s" % data
				continue

			response_event = None
			if isinstance(event, events.AuthenticationRequest):
				user = self.user_from_session_key(event.session_id)
				if user.is_authenticated():
					#print "Authed: %s" % user.username
					self.user = user
					response_event = events.AuthenticationResponse(True, user.username)
				else:
					print "Auth failure with session id %s" % event.session_id
					response_event = events.AuthenticationResponse(False)
			elif isinstance(event, events.PoolInfoRequest):
				if not self.user:
					print 'Attemped unauthed pool info request'
				else:
					space_infos = [{'name':sim.space.name, 'url':sim.space.get_absolute_url()} for sim in self.server.sim_pool.simulators]
					response_event = events.PoolInfo({ 'space_infos':space_infos })
			elif isinstance(event, events.JoinSpaceRequest):
				if not self.user:
					print 'Attemped unauthed join space'
					response_event = events.JoinSpaceResponse(event.space_id)
				else:
					try:
						space = Space.objects.get(pk=event.space_id)
						sim = self.server.sim_pool.get_simulator(space.id)
						if not sim: print 'Could not find a sim for space: %s' % space.id
						allow_join, space_member = Space.objects.get_membership(space, self.user)
						response_event = events.JoinSpaceResponse(space.id, allow_join)
						if allow_join:
							self.space_id = space.id
							try:
								response_event.scene_doc = to_json(sim.scene)
							except:
								print "Could not log in: %s" % pprint.pformat(traceback.format_exc())
						else:
							print 'Attempted disallowed join space'
						if space_member:
							response_event.is_member = True
							response_event.is_admin = space_member.is_admin
							response_event.is_editor = space_member.is_editor
					except:
						traceback.print_exc()
						response_event = events.JoinSpaceResponse(event.space_id)
			elif isinstance(event, events.TemplateUpdated):
				if self.user and self.user.is_staff:
					event.connection = self
					for simulator in self.server.sim_pool.simulators:
						simulator.event_queue.put(event)
			elif self.space_id:
				simulator = self.server.sim_pool.get_simulator(self.space_id)
				if simulator:
					event.connection = self
					simulator.event_queue.put(event)
				else:
					print "Received an event for an absent simulator %s" % event
			else:
				print "Received unhandled event %s" % event.to_json()

			if response_event:
				#print 'Outgoing: ', to_json(response_event)
				self.client_socket.send('\x00')
				self.client_socket.send(response_event.to_json())
				self.client_socket.send('\xff')
		self.finish()

	def user_from_session_key(self, session_key):
		"""Returns a User object if it is associated with a session key, otherwise None"""
		session_engine = __import__(settings.SESSION_ENGINE, {}, {}, [''])
		session_wrapper = session_engine.SessionStore(session_key)

		user_id = session_wrapper.get(SESSION_KEY)
		if user_id == None:
			return AnonymousUser()
		backend = session_wrapper.get(BACKEND_SESSION_KEY)
		if backend == None:
			session_wrapper.get(BACKEND_SESSION_KEY)
		auth_backend = load_backend(backend)
		if auth_backend == None:
			return AnonymousUser()	
		return auth_backend.get_user(user_id)
			
	def finish(self):
		"""Clean up the connection, remove this connection from the sim pool, and send a UserExited event to the simulator"""
		self.disconnected = True
		#print self.user, 'disconnected'
		self.server.ws_connections.remove(self)
		# alert the space (if any) that this user has exited only if there are no other connections for that user and space
		if self.space_id is None: return
		for connection in self.server.ws_connections:
			if self.user == connection.user and self.space_id == connection.space_id: return
		sim = self.server.sim_pool.get_simulator(self.space_id)
		if sim is not None:
			sim.event_queue.put(events.UserExited(self.space_id, self.user.username))
	def __unicode__(self):
		return "Connection: %s user: %s space: %s" % (self.client_address, self.user, self.space_id)	

class SimulationServer:
	"""
	Runs a Wind server and a sim pool.
	TODO: Allow the wind server to be separate.
	TODO: Allow multiple server pools.
	"""
	def __init__(self):
		self.wind_server = WindServer()
		self.sim_pool = sim_pool.SimulatorPool(self)
		self.ws_connections = []
		self.registration = None
		spaciblo.sim.DEFAULT_SIM_SERVER = self
		
	def start(self):
		self.wind_server.start()
		self.sim_pool.start_all_spaces()
		self.registration, created = SimulatorPoolRegistration.objects.get_or_create(ip=self.wind_server.ws_server.socket.getsockname()[0], port=self.wind_server.ws_server.port)

	def stop(self):
		if self.registration:
			try:
				self.registration.delete()
			except:
				traceback.print_exc()

		self.sim_pool.stop_all_spaces()
		self.wind_server.stop()
		

# Copyright 2010 Trevor F. Smith (http://trevor.smith.name/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
