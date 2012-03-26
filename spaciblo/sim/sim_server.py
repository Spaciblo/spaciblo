import sys
import time, datetime
import pprint, traceback
import Queue
import threading
import simplejson

from django.conf import settings
from django.contrib.auth import SESSION_KEY, BACKEND_SESSION_KEY, load_backend
from django.contrib.auth.models import AnonymousUser

from blank_slate.wind.events import parse_event_json
from blank_slate.wind.server import Server as WindServer
from blank_slate.wind.handler import to_json

import spaciblo.sim
import spaciblo.sim.sim_pool as sim_pool
import spaciblo.sim.events as events
from spaciblo.sim.models import Space, SimulatorPoolRegistration

class SimulationServer:
	"""
	Runs a Wind server and a sim pool.
	TODO: Allow the wind server to be separate.
	TODO: Allow multiple server pools.
	"""
	def __init__(self):
		self.wind_server = WindServer()
		self.sim_pool = sim_pool.SimulatorPool(self)
		self.ws_connections = []
		self.registration = None
		spaciblo.sim.DEFAULT_SIM_SERVER = self
		
	def start(self):
		self.wind_server.start()
		self.sim_pool.start_all_spaces()
		self.registration, created = SimulatorPoolRegistration.objects.get_or_create(ip=self.wind_server.ws_server.socket.getsockname()[0], port=self.wind_server.ws_server.port)

	def stop(self):
		if self.registration:
			try:
				self.registration.delete()
			except:
				traceback.print_exc()

		self.sim_pool.stop_all_spaces()
		self.wind_server.stop()
		

# Copyright 2010 Trevor F. Smith (http://trevor.smith.name/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
