"""The URLS for the API (not the user readable web UI)"""
import traceback

from django.conf.urls.defaults import *
from django.contrib.auth.models import User

from piston.resource import Resource

from models import TemplateHandler, AssetHandler, SpaceHandler

urlpatterns = patterns('',
	(r'^template/$', Resource(handler=TemplateHandler)),
	url(r'^template/(?P<id>[^/]+)/$', Resource(handler=TemplateHandler), name='template-api'),
	(r'^template/(?P<template_id>[\d]+)/asset/(?P<asset_key>[^/]+)$', 'spaciblo.sim.api_views.template_asset'),
	(r'^asset/$', Resource(handler=AssetHandler)),
	(r'^asset/(?P<id>[^/]+)/$', Resource(handler=AssetHandler)),
	(r'^space/$', Resource(handler=SpaceHandler)),
	(r'^space/(?P<id>[^/]+)/$', Resource(handler=SpaceHandler)),
	(r'^space/(?P<id>[^/]+)/scene/$', 'spaciblo.sim.api_views.scene_document'),
)
	
# Copyright 2010 Trevor F. Smith (http://trevor.smith.name/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
