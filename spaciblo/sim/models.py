import os
import shutil
import tarfile
import tempfile
import traceback

from django.db import models
from django.conf import settings
from django.core.files import File
from django.core.exceptions import *
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.files.storage import default_storage

from piston.handler import BaseHandler
from blank_slate.wind.handler import to_json
from blank_slate.wind.events import EventHandler

from glge import Scene
from sim_client import SimClient
from loaders.blender import JSONLoader
from loaders.obj import ObjLoader, MtlLibLoader

class HydrateModel(models.Model):
	
	@classmethod
	def type(cls):
		return cls.__name__
	@classmethod
	def dict(cls):
		return cls().__dict__
	
	class Meta:
		abstract = True

class SpaceManager(models.Manager):
	def get_membership(self, space, user):
		"""Returns a tuple of the form (allow_entry, SpaceMember) where allow_entry is True or False and SpaceMember will be None if there's no SpaceMember record for this user and space"""
		try:
			space_member = SpaceMember.objects.get(space=space, member=user)
		except:
			traceback.print_exc()
			space_member = None
		if space.state == 'closed': return (False, space_member)
		if space.state == 'admin_only' and (space_member == None or not space_member.is_admin): return (False, space_member)
		if space.max_guests > 0: return (True, space_member) #TODO respect the guest limits
		return (space_member != None, space_member)

def default_scene_doc(): return to_json(Scene())
			
class Space(HydrateModel):
	"""An n-dimensional cartesian space"""
	name = models.CharField(max_length=1000)
	slug = models.SlugField(max_length=1000)
	STATE_CHOICES = (('open', 'open'), ('admin_only', 'admin_only'), ('closed', 'closed'))
	state = models.CharField(max_length=20, choices=STATE_CHOICES, default='admin_only', blank=False, null=False)
	max_guests = models.IntegerField(blank=False, null=False, default=0)
	scene_document = models.TextField(blank=False, null=False, default=default_scene_doc)
	default_body = models.ForeignKey("Template", blank=False, null=False)
	
	objects = SpaceManager()

	def duplicate(self): return Space.objects.create(name=self.name, slug='%s 1' % self.slug, state=self.state, max_guests=self.max_guests, scene_document=self.scene_document, default_body=self.default_body)

	def add_member(self, user, is_admin=False, is_editor=False):
		membership, created = SpaceMember.objects.get_or_create(space=self, member=user)
		membership.is_admin = is_admin
		membership.is_editor = is_editor
		membership.save()

	@models.permalink
	def get_absolute_url(self): 
		return ('spaciblo.sim.views.space', (), { 'id':self.id })

	def __unicode__(self):
		return "Space #%s: %s" % (self.id, self.name)

class SpaceHandler(BaseHandler):
	model = Space
	fields = ('name', 'slug', ('default_body', ('id',)), 'id', 'state', 'max_guests')
	allowed_methods = ('GET',)

class SpaceMember(HydrateModel):
	"""A member of a space which can have admin or editor rights."""
	space = models.ForeignKey(Space, blank=False, null=False)
	member = models.ForeignKey(User, blank=False, null=False)
	is_admin = models.BooleanField(blank=False, default=False)
	is_editor = models.BooleanField(blank=False, default=False)

class SpaceMemberHandler:
	model = SpaceMember
	attributes = ('id', 'member', 'is_admin', 'is_editor')

class Asset(HydrateModel):
	"""A chunk of typed data used by a template to instantiate an Object in a Space."""
	APPLICATION_KEY = 'application'
	TYPE_CHOICES = (('geometry', 'geometry'), ('animation', 'animation'), ('script', 'script'), ('texture', 'texture'), ('text', 'text'), ('application', 'application'))
	file_type = models.CharField(max_length=20, choices=TYPE_CHOICES, blank=False, null=False, default='text')
	file = models.FileField(upload_to='asset/%Y/%m/%d', null=False, blank=False)
	prepped_file = models.FileField(upload_to='prepped/%Y/%m/%d', null=True, blank=True) # a version of this asset which is optimized for use, e.g. a JSON representation of a geometry
	
	def save(self, force_insert=False, force_update=False):
		"""Deletes old files if they exist for this asset"""
		try:
			if Asset.objects.filter(pk=self.pk).count() > 0:
				old_obj = Asset.objects.get(pk=self.pk)
				if self.file and old_obj.file and old_obj.file.path != self.file.path:
					default_storage.delete(old_obj.file.path)
				if self.prepped_file and old_obj.prepped_file and old_obj.prepped_file.path != self.prepped_file.path:
					default_storage.delete(old_obj.prepped_file.path)
		except:
			traceback.print_exc()
		super(Asset, self).save(force_insert, force_update)
	
	def __unicode__(self):
		return self.file.name

class AssetHandler(BaseHandler):
	model = Asset
	fields = ('id', 'file_type', 'file', 'prepped_file')
	allowed_methods = ('GET',)

	@classmethod
	def file(cls, asset):
		if asset.file: return asset.file.url
		return ""

	@classmethod
	def prepped_file(cls, asset):
		if asset.prepped_file: return asset.prepped_file.url
		return ""

class TemplateAsset(HydrateModel):
	"""A mediation record linking an asset with a template"""
	template = models.ForeignKey('Template', blank=False, null=False, related_name="templateassets")
	asset = models.ForeignKey(Asset, blank=False, null=False)
	key = models.CharField(max_length=1000, blank=False, null=False)
	def __unicode__(self):
		return "TemplateAsset: %s" % self.asset

class TemplateAssetHandler(BaseHandler):
	model = TemplateAsset
	fields = ('id', 'template', 'asset', 'key')
	allowed_methods = ('GET',)

class TemplateSetting(HydrateModel):
	"""A key/value tuple used to initialize an Object's state"""
	key = models.CharField(max_length=1000, blank=False, null=False)
	value = models.TextField(blank=False, null=False)
	def __unicode__(self):
		return "<%s|%s>" % (self.key, self.value)

class TemplateSettingHandler(BaseHandler):
	model = TemplateSetting
	fields = ('id', 'key', 'value')
	allowed_methods = ('GET',)

class TemplateChild(HydrateModel):
	"""A record of where a child template should be in relation to its parent."""
	template = models.ForeignKey('Template', blank=False, null=False)
	#TODO make position and orientation custom tuple fields
	position = models.CharField(max_length=1000, blank=False, null=False, default="0,0,0") # px, py, pz
	orientation = models.CharField(max_length=1000, blank=False, null=False, default="1,0,0,0") # qs,qx,qy,qz
	settings = models.ManyToManyField(TemplateSetting, blank=True, null=True) # overrides the child's setting defaults
	def __unicode__(self):
		return "TemplateChild: %s" % self.template
	class Meta:
		verbose_name_plural = 'template children'

class TemplateChildHandler(BaseHandler):
	model = TemplateChild
	fields = ('id', 'position', 'orientation', 'template', 'settings')

class Template(HydrateModel):
	"""A set of information used to instantiate an Object in a Space."""
	name = models.CharField(max_length=1000, blank=False, null=False, default="A Template")
	owner = models.ForeignKey(User, blank=False, null=False)
	last_updated = models.DateTimeField(auto_now=True, blank=False, null=False)
	assets = models.ManyToManyField('Asset', blank=True, null=True, through='TemplateAsset')
	settings = models.ManyToManyField(TemplateSetting, blank=True, null=True) # used as defaults when creating a new Object
	children = models.ManyToManyField(TemplateChild, blank=True, null=True, related_name="parents")
	#TODO make position and orientation custom tuple fields
	seat_position = models.CharField(max_length=1000, blank=True, null=True, default="0,0,0") # px, py, pz
	seat_orientation = models.CharField(max_length=1000, blank=True, null=True, default="1,0,0,0") # qs,qx,qy,qz

	def prep_assets(self):
		obj_assets = []
		mtl_assets = {}
		json_assets = []
		app_asset = None
		for template_asset in TemplateAsset.objects.filter(template=self):
			if template_asset.asset.file_type == 'geometry' and template_asset.asset.file.name.endswith('.mtl'):
				mtl_assets[template_asset.key] = template_asset.asset
			elif template_asset.asset.file_type == 'geometry' and template_asset.asset.file.name.endswith('.obj'):
				obj_assets.append(template_asset.asset)
			elif template_asset.asset.file_type == 'geometry' and template_asset.asset.file.name.endswith('.json'):
				json_assets.append(template_asset.asset)
			elif template_asset.asset.file_type == 'application':
				app_asset = template_asset.asset
			#else:
			#	print 'asset type %s' % template_asset.asset.type
		
		for json_asset in json_assets:
			loader = JSONLoader()
			json_string = open(json_asset.file.path).read()
			geometry = loader.toGeometry(json_string)
			if not geometry.name: geometry.name = self.name
			path = '/tmp/prepped_geo-%s' % self.id
			json_file = file(path, 'wb')
			json_file.write(to_json(geometry))
			json_file.close()
			json_file = file(path, 'r')
			json_asset.prepped_file.save(json_file.name, File(json_file), save=False)
			json_asset.save()
			json_file.close()
			os.unlink(path)
		
		for obj_asset in obj_assets: # try to save a prepped geometry JSON
			try:
				loader = ObjLoader()
				obj = loader.parse(open(obj_asset.file.path).read())
				if obj.mtllib and mtl_assets.has_key(obj.mtllib):
					mtllib_loader = MtlLibLoader()
					mtllib = mtllib_loader.parse(open(mtl_assets[obj.mtllib].file.path).read())
				elif obj.mtllib:
					print 'Obj asset %s requires an unknown mtllib: %s' % (obj_asset.file, obj.mtllib)
					mtllib = None
				else:
					print 'Obj has no mtllib'
					mtllib = None
				geometry = obj.toGeometry(mtllib)
				path = '/tmp/prepped_geo-%s' % self.id
				json_file = file(path, 'wb')
				json_file.write(to_json(geometry))
				json_file.close()
				json_file = file(path, 'r')
				obj_asset.prepped_file.save(json_file.name, File(json_file), save=False)
				obj_asset.save()
				json_file.close()
				os.unlink(path)
			except:
				traceback.print_exc()
		
		if app_asset != None:
			target_dir = os.path.join(settings.TEMPLATE_APPS_DIR, self.template_app_module_name)
			if os.path.exists(target_dir): shutil.rmtree(target_dir)
			tar = tarfile.open(app_asset.file.path)
			tar.extractall(path=target_dir)
			tar.close()

	def get_key(self, asset):
		try:
			return TemplateAsset.objects.get(template=self, asset=asset).key
		except ObjectDoesNotExist:
			return None

	def get_asset(self, key):
		try:
			return TemplateAsset.objects.get(template=self, key=key).asset
		except ObjectDoesNotExist:
			return None

	@property
	def template_app_module_name(self): return "template_%s" % self.id

	@models.permalink
	def get_absolute_url(self): return ('spaciblo.sim.views.template', (), { 'id':self.id })

	@models.permalink
	def get_api_url(self): return ('template-api', (), { 'id':self.id })

	def __unicode__(self):
		return self.name

class TemplateHandler(BaseHandler):
	model = Template
	fields = ('id', 'owner', 'seat_orientation', 'seat_position', 'last_updates', 'name', 'settings', 'children', 'assets')
	allowed_methods = ('GET',)

	@classmethod
	def assets(cls, template): return [{'asset': ta.asset, 'id':ta.id, 'key': ta.key} for ta in template.templateassets.all()]

class SimulatorPoolRegistrationManager(models.Manager):
	def broadcast_event(self, session_key, space_id, event):
		for reg in self.all(): reg.send_event(session_key, space_id, event)
			

class SimulatorPoolRegistration(models.Model):
	"""A simulator pool address in this cluster"""
	ip = models.IPAddressField()
	port = models.IntegerField()
	
	objects = SimulatorPoolRegistrationManager()

	def send_event(self, session_key, space_id, event):
		event_handler = EventHandler()
		sim_client = SimClient(session_key, self.ip, self.port, '%s:80' % self.ip, event_handler.handle_event)
		sim_client.authenticate()
		auth_event = event_handler.events.get(True, 10)
		if not auth_event.authenticated: raise Exception('SimulatorPoolRegistration could not authenticate against the simulator pool')
		sim_client.join_space(space_id)
		join_event = event_handler.events.get(True, 10)
		if not join_event.joined: raise Exception('SimulatorPoolRegistration could not join the space channel: %s' % space_id)
		sim_client.send_event(event)
		sim_client.close()
	
	def fetch_pool_info(self, session_key):
		try:
			event_handler = EventHandler()
			sim_client = SimClient(session_key, self.ip, self.port, '%s:80' % self.ip, event_handler.handle_event)
			sim_client.authenticate()
			event = event_handler.events.get(True, 10)
			if not event.authenticated: raise Exception('Could not authenticate against the simulator pool')
			sim_client.request_pool_info()
			event = event_handler.events.get(True, 10)
			sim_client.close()
			return event.infos
		except:
			traceback.print_exc()
			return []

HYDRATE_MODELS = [Template, TemplateChild, TemplateSetting, TemplateAsset, Asset, SpaceMember, Space]

# Copyright 2010 Trevor F. Smith (http://trevor.smith.name/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
