import os
import csv
import ConfigParser
import tarfile
import tempfile
import simplejson

from django.template.defaultfilters import slugify
from django.core.management.base import NoArgsCommand, CommandError
from django.core.files import File

class Command(NoArgsCommand):
	"""Loads the example templates and spaces."""
	help = "Loads the example templates and spaces."

	requires_model_validation = True

	def handle_noargs(self, **options):
		from django.contrib.auth.models import User
		from spaciblo.sim.loaders.dir_loaders import TemplateDirLoader, SpaceDirLoader
		from spaciblo.sim.management import *
		from blank_slate.wind.handler import to_json
		
		if len(User.objects.filter(is_staff=True)) == 0:
			print 'There must be at least one staff user before we can load templates.'
			return
		
		admin_user = User.objects.filter(is_staff=True).order_by('id')[0]
		
		for template_dir in os.listdir(TEMPLATE_DIR_PATH):
			abs_dir = os.path.join(TEMPLATE_DIR_PATH, template_dir)
			if not os.path.isdir(abs_dir): continue
			template = TemplateDirLoader().load(abs_dir, admin_user)
			#print 'loaded template: ', template
		
		for space_dir in os.listdir(SPACE_DIR_PATH):
			abs_dir = os.path.join(SPACE_DIR_PATH, space_dir)
			if not os.path.isdir(abs_dir): continue
			space = SpaceDirLoader().load(abs_dir, admin_user)
			#print 'loaded space: ', space

# Copyright 2010 Trevor F. Smith (http://trevor.smith.name/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
