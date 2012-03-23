"""A Django app for simulating and service Spaciblo spaces."""

# Copyright 2010 Trevor F. Smith (http://trevor.smith.name/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

from django.contrib.auth.models import User
from piston.handler import BaseHandler, AnonymousBaseHandler
BaseHandler.fields = AnonymousBaseHandler.fields = ()

class UserHandler(BaseHandler):
	"""The Piston handler for Django's user accounts"""
	model = User
	fields = ('username', 'first_name', 'last_name')
	allowed_methods = ('GET',)

DEFAULT_SIM_SERVER = None