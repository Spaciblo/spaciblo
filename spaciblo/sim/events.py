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

	def handle_subscribe_request(self, connection, event):
		import spaciblo.sim
		allow_join, space_member = spaciblo.sim.models.Space.objects.get_membership(self.space, connection.user)
		return (allow_join, SubscribeResponse(channel_id=self.channel_id, joined=allow_join))

	@classmethod
	def generate_channel_id(cls, space_id): return 'space_%s' % space_id

	@classmethod
	def parse_channel_id(cls, channel_id):
		"""Returns the space ID"""
		tokens = channel_id.split('_')
		if len(tokens) != 2 or tokens[0] != 'space': raise Exception('Bad channel_id %s %s' % (channel_id, tokens))
		return int(tokens[1])

class AddUserRequest(Event):
	"""Request a body in a space."""
	def __init__(self, position=None, orientation=None):
		if not position: position = [0,0,0]
		if not orientation: orientation = [0,0,0,1]
		self.position = position
		self.orientation = orientation

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
			response_event.position = self.position
			response_event.orientation = self.orientation
			print 'Getting scene doc:', connection.channel.space.id, [sim.space.id for sim in spaciblo.sim.DEFAULT_SIM_SERVER.sim_pool.simulators]
			response_event.scene_doc = to_json(spaciblo.sim.DEFAULT_SIM_SERVER.sim_pool.get_simulator(connection.channel.space.id).scene)
		if space_member:
			response_event.is_member = True
			response_event.is_admin = space_member.is_admin
			response_event.is_editor = space_member.is_editor
		#print 'Sending response %s' % response_event.to_json()
		connection.send_event(response_event)
		if allow_join: connection.channel.send_event(UserAdded(connection.user.username, self.position, self.orientation))

class AddUserResponse(Event):
	"""Indicate whether an AddUserRequest is successful and what role the client may play (e.g. member, editor, ...)."""
	def __init__(self, joined=False, position=None, orientation=None, is_member=False, is_editor=False, is_admin=False, scene_doc=None):
		self.joined = joined
		self.position = position
		self.orientation = orientation
		self.is_member = is_member
		self.is_editor = is_editor
		self.is_admin = is_admin
		self.scene_doc = scene_doc

class UserAdded(Event):
	def __init__(self, username=None, position=None, orientation=None):
		self.username = username
		self.position = position
		self.orientation = orientation

class UserExited(Event):
	def __init__(self, username=None):
		self.username = username

class UserMoveRequest(ForwardingEvent):
	"""A space client sends this to indicate that the user has requested a motion."""
	def __init__(self, username=None, position=None, orientation=None):
		if not position: position = [0,0,0]
		if not orientation: orientation = [0,0,0,1]
		self.username = username
		self.position = position
		self.orientation = orientation

class PlaceableMoved(ForwardingEvent):
	"""The simulator generates these to indicate that a Placeable is in motion."""
	def __init__(self, uid=None, position=None, orientation=None):
		if not position: position = [0,0,0]
		if not orientation: orientation = [0,0,0,1]
		self.uid = uid;
		self.position = position
		self.orientation = orientation

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
