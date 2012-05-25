import Queue
import threading
import random
import datetime
import logging
import simplejson

from blank_slate.wind.client import Client
from blank_slate.wind.events import Heartbeat, AuthenticationResponse, SubscribeResponse, parse_event_json

import spaciblo.sim.events as events
from spaciblo.sim.glge import Scene, Group, Object

class SimClient:
	def __init__(self, session_key, ws_host, ws_port, ws_origin, event_handler=None):
		self.ws_client = Client(session_key, ws_host, ws_port, ws_origin, self.handle_event)
		self.event_handler = event_handler
		self.username = None
		self.space_id = None
		self.is_member = None
		self.is_editor = None
		self.is_admin = None
		self.scene = None

	def handle_event(self, event):
		if event == None: return

		if isinstance(event, AuthenticationResponse):
			if event.authenticated:
				self.username = event.username
		elif isinstance(event, SubscribeResponse):
			if event.joined:
				self.space_id = events.SpaceChannel.parse_channel_id(event.channel_id)
		elif isinstance(event, events.AddUserResponse):
			if event.joined:
				self.is_member = event.is_member
				self.is_editor = event.is_editor
				self.is_admin = event.is_admin
				self.scene = Scene().populate(simplejson.loads(event.scene_doc))
		elif isinstance(event, events.UserAdded):
			pass
		elif isinstance(event, events.UserExited):
			user_node = self.scene.get_user(event.username)
			if user_node: self.scene.remove_node(user_node)
		elif isinstance(event, events.NodeAdded):
			json = simplejson.loads(event.json_data)
			if 'children' in json:
				node = Group().populate(json)
			else:
				node = Object().populate(json)
			parent = self.scene.get_node(event.parent_id)
			parent.children.append(node)
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

	def join_space(self, space_id): self.ws_client.subscribe(events.SpaceChannel.generate_channel_id(space_id))

	def add_user(self): self.ws_client.send_event(events.AddUserRequest())
	
	def notify_template_updated(self, template_id, url, key=None): self.ws_client.send_event(events.TemplateUpdated(template_id, url, key))

	def request_pool_info(self): self.ws_client.send_event(events.PoolInfoRequest())

	def send_event(self, event): self.ws_client.send_event(event)

	def close(self):
		self.should_run = False
		self.ws_client.close()
