import Queue
import threading
import random
import datetime
import logging
import simplejson

from django.contrib.sessions.models import Session
import django.contrib.sessions.backends.db as session_engine
from django.contrib.auth import BACKEND_SESSION_KEY, SESSION_KEY, authenticate

from blank_slate.wind.client import Client
from blank_slate.wind.events import Heartbeat, AuthenticationResponse, parse_event_json

import spaciblo.sim.events as events
from spaciblo.sim.glge import Scene, Group, Object

class SimClient:
	def __init__(self, session_key, ws_host, ws_port, ws_origin, event_handler=None):
		self.ws_client = Client(session_key, ws_host, ws_port, ws_origin, self.handle_event)
		self.event_handler = event_handler
		self.username = None
		self.space_id = None
		self.scene = None

	def handle_event(self, event):
		if isinstance(event, AuthenticationResponse):
			if event.authenticated:
				self.username = event.username
		elif isinstance(event, events.JoinSpaceResponse):
			if event.joined:
				self.space_id = event.space_id
				self.scene = Scene().populate(simplejson.loads(event.scene_doc))
		elif isinstance(event, events.NodeAdded):
			json = simplejson.loads(event.json_data)
			if 'children' in json:
				node = Group().populate(json)
			else:
				node = Object().populate(json)
			parent = self.scene.get_node(event.parent_id)
			parent.children.append(node)
		elif isinstance(event, events.UserExited):
			user_node = self.scene.get_user(event.username)
			if user_node: self.scene.remove_node(user_node)
		elif isinstance(event, events.PlaceableMoved):
			node = self.scene.get_node(event.uid)
			if node:
				print 'should set the new node position'
				#thing.position = Position().hydrate(event.position)
				#thing.orientation = Orientation().hydrate(event.orientation)
		elif isinstance(event, events.PoolInfo) or isinstance(event, events.TemplateUpdated) or isinstance(event, Heartbeat):
			pass # don't care
		else:
			print 'Unhandled incoming space event: %s' % event

		if self.event_handler: self.event_handler(event)


	def authenticate(self): self.ws_client.authenticate()

	def join_space(self, space_id): self.ws_client.send_event(events.JoinSpaceRequest(space_id))

	def add_user(self): self.ws_client.send_event(events.AddUserRequest(self.space_id, self.username))
	
	def notify_template_updated(self, template_id, url, key=None): self.ws_client.send_event(events.TemplateUpdated(self.space_id, template_id, url, key))

	def request_pool_info(self): self.ws_client.send_event(events.PoolInfoRequest())

	def send_event(self, event): self.ws_client.send_event(event)

	def close(self):
		self.should_run = False
		self.ws_client.close()
