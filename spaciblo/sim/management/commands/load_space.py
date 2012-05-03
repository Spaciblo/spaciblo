import os
import csv
import tarfile
import tempfile
import simplejson
import ConfigParser

from optparse import make_option

from django.core.files import File
from django.template.defaultfilters import slugify
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
	help = "Loads a space from a directory."
	requires_model_validation = True

	def handle(self, *args, **options):
		from django.contrib.auth.models import User
		from spaciblo.sim.loaders.dir_loaders import TemplateDirLoader, SpaceDirLoader
		from spaciblo.sim.management import SPACE_DIR_PATH

		if len(User.objects.filter(is_staff=True)) == 0:
			print 'There must be at least one staff user before we can load templates.'
			return
		
		admin_user = User.objects.filter(is_staff=True).order_by('id')[0]

		if len(args) == 0:
			print 'You must specify a directory from which to read the space information'
			return

		full_path = os.path.abspath(args[0])
		if not os.path.isdir(full_path):
			print '"%s" is not a directory' % full_path
			return
		space = SpaceDirLoader().load(full_path, admin_user)

# Copyright 2010 Trevor F. Smith (http://trevor.smith.name/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
