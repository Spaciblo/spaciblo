import os
import sys
import csv
import tarfile
import tempfile
import simplejson
import ConfigParser

from optparse import make_option

from django.contrib.sessions.models import Session
from django.core.management.base import BaseCommand, CommandError

from blank_slate.wind.handler import to_json
from spaciblo.sim.sim_client import SimClient

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
			print 'Usage: ./manage.py export_space <space id> <path to things.csv>'
			return
		space_id = int(args[0])
		if Space.objects.filter(pk=space_id).count() == 0:
			print 'Invalid space id: %s' % space_id
			return
		space = Space.objects.get(pk=space_id)

		full_path = os.path.abspath(args[1])
		space_dir_path, things_file_name = os.path.split(full_path)
		if not os.path.isdir(space_dir_path):
			print 'Could not find directory', space_dir_path
			return
		things_file = open(full_path, mode='w')

		if SimulatorPoolRegistration.objects.all().count() == 0:
			print 'No simulators are running'
			return
		pool_registration = SimulatorPoolRegistration.objects.all()[0]

		event_handler = EventHandler()
		session_key = self.get_session_key(admin_user)
		try:
			sim_client = SimClient(session_key, pool_registration.ip, pool_registration.port, '%s:80' % pool_registration.ip, event_handler.handle_event)

			sim_client.authenticate()
			auth_event = event_handler.events.get(True, 10)
			if not auth_event.authenticated: 
				print 'Could not authenticate using key %s' % session_key
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

			things_csv = generate_things_csv(sim_client.scene)
			things_file.write(things_csv)
		finally:
			sim_client.close()


	def get_session_key(self, user):
		for session in Session.objects.all():
			data = session.get_decoded()
			if data.has_key('_auth_user_id') and data['_auth_user_id'] == user.id: return session.session_key
		return None

def generate_things_csv(scene):
	things = []
	for child in scene.children:
		if child.username: continue
		if not child.group_template: continue
		result = [child.group_template.name, child.locX, child.locY, child.locZ, child.quatX, child.quatY, child.quatZ, child.quatW, child.scaleX, child.scaleY, child.scaleZ]
		things.append(','.join([str(item) for item in result]))
	return '\n'.join(things)

# Copyright 2010 Trevor F. Smith (http://trevor.smith.name/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
