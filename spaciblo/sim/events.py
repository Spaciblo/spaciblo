"""The events used in the simulators.
The hydration code assumes that these event objects have only string attributes and has a no-param __init__.
"""
import traceback

from django.db.models.base import ObjectDoesNotExist

from blank_slate.wind.events import Event, ForwardingEvent, Channel, SubscribeResponse
from blank_slate.wind.handler import to_json

# TODO: Create a ForwardingEvent which only lets through the simulator originated events

class SpaceChannel(Channel):
	"""Handles events for a single Space"""

	def __init__(self, server, channel_id, name=None, options=None):
		from models import Space
		super(SpaceChannel, self).__init__(server, channel_id, name, options)
		self.space = Space.objects.get(pk=SpaceChannel.parse_channel_id(channel_id))
		self.sim_connection = None

	def handle_subscribe_request(self, connection, event):
		import spaciblo.sim
		allow_join, space_member = spaciblo.sim.models.Space.objects.get_membership(self.space, connection.user)
		return (allow_join, SubscribeResponse(channel_id=self.channel_id, joined=allow_join))

	def handle_disconnect(self, connection):
		if not connection.user: return
		if not self.sim_connection: return
		all_connections = self.server.get_client_connections(self.channel_id)
		for con in all_connections:
			if con == self.sim_connection: continue
			if con.user == connection.user:
				# Do not send the user existed event because another connection is owned by that user
				# This happens sometimes when the user hits reload and their browser makes a new connection before closing the old one
				return
		self.sim_connection.send_event(UserExited(username=connection.user.username))

	@classmethod
	def generate_channel_id(cls, space_id): return 'space_%s' % space_id

	@classmethod
	def parse_channel_id(cls, channel_id):
		"""Returns the space ID"""
		tokens = channel_id.split('_')
		if len(tokens) != 2 or tokens[0] != 'space': raise Exception('Bad channel_id %s %s' % (channel_id, tokens))
		return int(tokens[1])

class RegisterSimulator(Event):
	"""Note that this connection is the one to the simulator"""
	def service(self, connection):
		if connection.user == None:
			print 'Register sim not authed %s' % connection.user
			return
		if connection.channel == None:
			print 'Cannot register a sim without a channel %s' % connection.user
			return
		if not connection.user.is_staff:
			print 'Tried to register as sim without a staff account'
			return
		if connection.channel.sim_connection != None:
			print 'Already have a sim connection for this channel'
			return
		connection.channel.sim_connection = connection

class AddUserRequest(Event):
	"""Request a body in a space."""
	def __init__(self, location=None, quat=None):
		if not location: location = [0,0,0]
		if not quat: quat = [0,0,0,1]
		self.location = location
		self.quat = quat

	def service(self, connection):
		import spaciblo.sim
		if connection.user == None:
			print 'Add user not authed %s' % connection.user
			connection.send_event(AddUserResponse(joined=False))
			return
		if connection.channel == None:
			print 'Cannot join a space without first joining a channel %s' % connection.user
			connection.send_event(AddUserResponse(joined=False))
			return
		if connection.channel.space == None:
			print 'User (%s) cannot join a spaceless channel %s' % (connection.user, connection.space)
			connection.send_event(AddUserResponse(joined=False))
			return

		allow_join, space_member = spaciblo.sim.models.Space.objects.get_membership(connection.channel.space, connection.user)
		response_event = AddUserResponse(allow_join)
		if allow_join:
			response_event.location = self.location
			response_event.quat = self.quat
			response_event.scene_doc = to_json(spaciblo.sim.DEFAULT_SIM_SERVER.sim_pool.get_simulator(connection.channel.space.id).scene)
		if space_member:
			response_event.is_member = True
			response_event.is_admin = space_member.is_admin
			response_event.is_editor = space_member.is_editor
		#print 'Sending response %s' % response_event.to_json()
		connection.send_event(response_event)
		if allow_join: connection.channel.send_event(UserAdded(connection.user.username, self.location, self.quat))

class AddUserResponse(Event):
	"""Indicate whether an AddUserRequest is successful and what role the client may play (e.g. member, editor, ...)."""
	def __init__(self, joined=False, location=None, quat=None, is_member=False, is_editor=False, is_admin=False, scene_doc=None):
		self.joined = joined
		self.location = location
		self.quat = quat
		self.is_member = is_member
		self.is_editor = is_editor
		self.is_admin = is_admin
		self.scene_doc = scene_doc

class UserAdded(Event):
	def __init__(self, username=None, location=None, quat=None):
		self.username = username
		self.location = location
		self.quat = quat

class UserExited(Event):
	def __init__(self, username=None):
		self.username = username

class UserMoveRequest(ForwardingEvent):
	"""A space client sends this to indicate that the user has requested a motion."""
	def __init__(self, username=None, location=None, quat=None):
		if not location: location = [0,0,0]
		if not quat: quat = [0,0,0,1]
		self.username = username
		self.location = location
		self.quat = quat

class MovePlaceable(Event):
	"""A client sends this to request that a Placeable move"""
	def __init__(self, uid=None, location=None, quat=None):
		if not location: location = [0,0,0]
		if not quat: quat = [0,0,0,1]
		self.uid = uid;
		self.location = location
		self.quat = quat	

	def service(self, connection):
		connection.channel.sim_connection.send_event(self)

class PlaceableMoved(ForwardingEvent):
	"""The simulator generates these to indicate that a Placeable is in motion."""
	def __init__(self, uid=None, location=None, quat=None):
		if not location: location = [0,0,0]
		if not quat: quat = [0,0,0,1]
		self.uid = uid;
		self.location = location
		self.quat = quat

class NodeRemoved(ForwardingEvent):
	"""The simulator generates these to indicate that a Node has been destroyed."""
	def __init__(self, uid=None):
		self.uid = uid

class NodeAdded(ForwardingEvent):
	"""The simulator generates these to indicate that a Node as been created."""
	def __init__(self, parent_id=None, json_data=None):
		self.parent_id = parent_id
		self.json_data = json_data

class TemplateUpdated(ForwardingEvent):
	"""Notification that a template's data has been updated.  Renderers may choose to reload the template"""
	def __init__(self, template_id=None, url=None, key=None):
		self.template_id = template_id
		self.url = url
		self.key = key

class UserMessage(ForwardingEvent):
	"""A user generated chat message."""
	def __init__(self, username=None, message=None):
		self.username = username
		self.message = message
	def __repr__(self):
		return 'UserMessage: %s, %s' % (self.username, self.message)

class PoolInfoRequest(Event):
	"""Used to request stats information about the spaces in the pool."""
	def service(self, connection):
		# TODO send the pool info?
		connection.send_event(PoolInfo())

class PoolInfo(Event):
	"""Information about the spaces in the pool."""
	def __init__(self, infos=None):
		"""Infos MUST be maps of simple python times"""
		if not infos: infos = []
		self.infos = infos


# Copyright 2010,2011,2012 Trevor F. Smith (http://trevor.smith.name/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
