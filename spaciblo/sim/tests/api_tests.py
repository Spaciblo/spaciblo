from django.contrib.auth.models import User
from django.test import TestCase, TransactionTestCase, Client
from django.core.urlresolvers import reverse

import simplejson as json

from spaciblo.sim.models import *
from spaciblo.sim.management.commands.load_example_spaces import Command

class APITest(TestCase): 
	"""A test suite for the web API"""

	fixtures = ['auth.json', 'sites.json']
	root_url = '/api/sim/'
	
	def setUp(self):
		self.client = Client()
		self.command = Command()
		self.command.handle_noargs()

	def tearDown(self):
		pass

	def test_web_api(self):
		spaces = Space.objects.all()
		self.assertTrue(len(spaces) > 0)
		response = self.client.get(reverse('spaciblo.sim.api_views.scene_document', kwargs={ 'id':spaces[0].id }))
		self.assertEqual(response.status_code, 200)
		parsed_scene = json.loads(response.content)
		templates = Template.objects.all()
		self.assertTrue(len(templates) > 0)
		self.assertTrue(len(templates[0].assets.all()) > 0)
		asset = templates[0].assets.all()[0]
		response = self.client.get(reverse('spaciblo.sim.api_views.template_asset', kwargs={'template_id':templates[0].id, 'asset_key':templates[0].get_key(asset)}))
		self.assertEqual(response.status_code, 302) # the template asset view redirects to the static file url
		response = self.client.get(reverse('spaciblo.sim.api_views.template_asset', kwargs={'template_id':templates[0].id, 'asset_key':templates[0].get_key(asset)}), follow=True)
		self.assertEqual(response.status_code, 200)
		response = self.client.get('/api/sim/space/%s' % spaces[0].id, follow=True)
		self.assertEqual(response.status_code, 200)
		self.assertTrue(self.client.login(username='trevor', password='1234'))
