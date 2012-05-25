import os
import sys
import csv
import tarfile
import tempfile
import simplejson
import ConfigParser

from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from blank_slate.wind.handler import to_json
from spaciblo.sim.sim_client import SimClient
from spaciblo.sim.glge import Light, L_SPOT, L_DIR, L_POINT, L_OFF

class Command(BaseCommand):
	help = "Writes the info from a space to a directory."
	requires_model_validation = True

	def handle(self, *args, **options):
		from django.contrib.auth.models import User
		from blank_slate.wind.events import EventHandler, register_app_events
		register_app_events()

		from spaciblo.sim.management import SPACE_DIR_PATH
		from spaciblo.sim.models import SimulatorPoolRegistration, Space
		from spaciblo.sim.loaders.dir_loaders import TemplateDirLoader, SpaceDirLoader
		
		admin_user = User.objects.filter(is_staff=True).order_by('id')[0]

		if len(args) != 2:
			print 'Usage: ./manage.py export_space <space id> <path to space directory>'
			return
		space_id = int(args[0])
		if Space.objects.filter(pk=space_id).count() == 0:
			print 'Invalid space id: %s' % space_id
			return
		space = Space.objects.get(pk=space_id)

		space_dir_path = os.path.abspath(args[1])
		if not os.path.isdir(space_dir_path):
			print 'Could not find directory', space_dir_path
			return

		if SimulatorPoolRegistration.objects.all().count() == 0:
			print 'No simulators are running'
			return
		pool_registration = SimulatorPoolRegistration.objects.all()[0]

		event_handler = EventHandler()
		try:
			sim_client = SimClient(admin_user.session_key, pool_registration.ip, pool_registration.port, '%s:80' % pool_registration.ip, event_handler.handle_event)

			sim_client.authenticate()
			auth_event = event_handler.events.get(True, 10)
			if not auth_event.authenticated: 
				print 'Could not authenticate using key %s' % admin_user.session_key
				return

			sim_client.join_space(space.id)
			join_event = event_handler.events.get(True, 10)
			if not join_event.joined: 
				print 'Could not join the space channel: %s' % space_id
				return

			sim_client.add_user()
			add_event = event_handler.events.get(True, 10)
			if not add_event.joined: 
				print 'Could not add a user: %s' % space_id
				return

			things_file = open(os.path.join(space_dir_path, 'things.csv'), mode='w')
			things_csv = generate_things_csv(sim_client.scene)
			things_file.write(things_csv)

			lights_file = open(os.path.join(space_dir_path, 'lights.csv'), mode='w')
			lights_csv = generate_lights_csv(sim_client.scene)
			lights_file.write(lights_csv)
		finally:
			sim_client.close()


def generate_lights_csv(scene):
	lights = []
	for child in scene.children:
		if child.__class__ != Light: continue
		if child.type == L_POINT:
			type_name = 'point'
		elif child.type == L_DIR:
			type_name = 'directional'
		elif child.type == L_SPOT:
			type_name = 'spot'
		elif child.type == L_OFF:
			type_name = 'off'
		else:
			print 'Unknown light type:', child.type

		result = [type_name, child.locX, child.locY, child.locZ, child.quatX, child.quatY, child.quatZ, child.quatW, child.distance, child.specular]
		lights.append(','.join([str(item) for item in result]))
	return '\n'.join(lights)

def generate_things_csv(scene):
	things = []
	for child in scene.children:
		if child.__class__ == Light: continue
		if child.username: continue
		if not child.group_template: continue
		result = [child.group_template.name, child.locX, child.locY, child.locZ, child.quatX, child.quatY, child.quatZ, child.quatW, child.scaleX, child.scaleY, child.scaleZ]
		things.append(','.join([str(item) for item in result]))
	return '\n'.join(things)

# Copyright 2010 Trevor F. Smith (http://trevor.smith.name/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
