import os
import time
import urllib
import datetime
import sys
import tempfile
import shutil

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.contrib.sessions.models import Session

class Command(BaseCommand):
	help = "Creates a template using the files in a directory"
	args = "[owner_username,template_dir_path]"
	requires_model_validation = True

	def get_session_key(self, user):
		for session in Session.objects.all():
			data = session.get_decoded()
			if data.has_key('_auth_user_id') and data['_auth_user_id'] == user.id: return session.session_key
		return None

	def handle(self, *labels, **options):
		from django.contrib.auth.models import User
		from spaciblo.sim.loaders.dir_loaders import TemplateDirLoader
		from spaciblo.sim.models import SimulatorPoolRegistration
		from spaciblo.sim.events import TemplateUpdated
		
		if not labels or len(labels) != 2: raise CommandError('Enter two arguments, the owner username and the path to the template directory.')

		username = labels[0]
		if User.objects.filter(username=username).count() != 1: raise CommandError("No such user: %s" % username)
		owner = User.objects.get(username=username)

		template_path = os.path.realpath(labels[1])
		if not os.path.isdir(template_path): raise CommandError('The specified path "%s" is not a directory.' % template_path)

		template = TemplateDirLoader().load(template_path, owner)
		session_key = self.get_session_key(owner)
		#if session_key:
		#	SimulatorPoolRegistration.objects.broadcast_event(session_key, TemplateUpdated(-1, template.id, template.get_api_url()))
		sys.exit()
