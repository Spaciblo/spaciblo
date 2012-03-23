import os
import sys
import time

from django.core.management.base import NoArgsCommand, CommandError

class Command(NoArgsCommand):
	"""Runs the spaciblo simulation server."""
	help = "Runs the spaciblo simulation server."

	requires_model_validation = True

	def handle_noargs(self, **options):
		from spaciblo.sim.sim_server import SimulationServer
		sim_server = SimulationServer()
		sim_server.start()
		try:
			while True: time.sleep(10000000)
		except (KeyboardInterrupt, SystemExit):
			sim_server.stop()
			sys.exit()
		

# Copyright 2010 Trevor F. Smith (http://trevor.smith.name/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
