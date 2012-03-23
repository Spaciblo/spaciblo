"""The events used in the simulators.
The hydration code assumes that these event objects have only string attributes and has a no-param __init__.
"""
import traceback

from django.db.models.base import ObjectDoesNotExist

from blank_slate.wind.events import Event
from blank_slate.wind.handler import to_json

class JoinSpaceRequest(Event):
	"""A request from a space client to join a space."""
	def __init__(self, space_id=None):
		self.space_id = space_id

	def service(self, connection):
		from models import Space
		import spaciblo.sim
		if not connection.user:
			print 'Join not authed %s' % self.to_json()
			connection.send_event(JoinSpaceResponse(space_id=self.space_id, joined=False))
			return
		try:
			space = Space.objects.get(pk=self.space_id)
		except ObjectDoesNotExist:
			print 'No such space %s' % self.to_json()
			connection.send_event(JoinSpaceResponse(space_id=self.space_id, joined=False))
			return
		allow_join, space_member = Space.objects.get_membership(space, connection.user)
		response_event = JoinSpaceResponse(space.id, allow_join)
		if allow_join:
			response_event.scene_doc = to_json(spaciblo.sim.DEFAULT_SIM_SERVER.sim_pool.get_simulator(space.id).scene)
		if space_member:
			response_event.is_member = True
			response_event.is_admin = space_member.is_admin
			response_event.is_editor = space_member.is_editor
		#print 'Sending response %s' % response_event.to_json()
		connection.send_event(response_event)

class JoinSpaceResponse(Event):
	"""A response from the SimServer indicating whether a JoinSpaceRequest is successful and what role the client may play (e.g. member, editor, ...)."""
	def __init__(self, space_id=None, joined=False, is_member=False, is_editor=False, is_admin=False, scene_doc=None):
		self.space_id = space_id
		self.joined = joined
		self.is_member = is_member
		self.is_editor = is_editor
		self.is_admin = is_admin
		self.scene_doc = scene_doc

class UserExited(Event):
	"""An event which is generated when a user exists a space."""
	def __init__(self, space_id=None, username=None):
		self.space_id = space_id
		self.username = username

class AddUserRequest(Event):
	"""A space client may send an AddUserRequest if they require a body in a space."""
	def __init__(self, space_id=None, username=None, position=None, orientation=None):
		if not position: position = [0,0,0]
		if not orientation: orientation = [0,0,0,1]
		self.space_id = space_id
		self.username = username
		self.position = position
		self.orientation = orientation

class UserMoveRequest(Event):
	"""A space client sends this to indicate that the user has requested a motion."""
	def __init__(self, space_id=None, username=None, position=None, orientation=None):
		if not position: position = [0,0,0]
		if not orientation: orientation = [0,0,0,1]
		self.space_id = space_id
		self.username = username
		self.position = position
		self.orientation = orientation

class PlaceableMoved(Event):
	"""The simulator generates these to indicate that a Placeable is in motion."""
	def __init__(self, space_id=None, uid=None, position=None, orientation=None):
		if not position: position = [0,0,0]
		if not orientation: orientation = [0,0,0,1]
		self.space_id = space_id
		self.uid = uid;
		self.position = position
		self.orientation = orientation

class NodeRemoved(Event):
	"""The simulator generates these to indicate that a Node has been destroyed."""
	def __init__(self, space_id=None, uid=None):
		self.space_id = space_id
		self.uid = uid

class NodeAdded(Event):
	"""The simulator generates these to indicate that a Node as been created."""
	def __init__(self, space_id=None, parent_id=None, json_data=None):
		self.space_id = space_id
		self.parent_id = parent_id
		self.json_data = json_data

class TemplateUpdated(Event):
	"""Notification that a template's data has been updated.  Renderers may choose to reload the template"""
	def __init__(self, space_id=None, template_id=None, url=None, key=None):
		self.space_id = space_id
		self.template_id = template_id
		self.url = url
		self.key = key

class UserMessage(Event):
	"""A user generated chat message."""
	def __init__(self, space_id=None, username=None, message=None):
		self.space_id = space_id
		self.username = username
		self.message = message
	def __repr__(self):
		return 'UserMessage: %s, %s, %s' % (self.space_id, self.username, self.message)

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

#SIM_EVENTS = [Heartbeat, UserMessage, PlaceableMoved, AuthenticationRequest, AuthenticationResponse, JoinSpaceRequest, JoinSpaceResponse, UserMoveRequest, AddUserRequest, NodeAdded, NodeRemoved, TemplateUpdated, PoolInfoRequest, PoolInfo]


# Copyright 2010,2011,2012 Trevor F. Smith (http://trevor.smith.name/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
