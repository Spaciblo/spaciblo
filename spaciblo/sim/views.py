import datetime
import calendar
import pprint
import traceback

from django.conf import settings
from django.db.models import Q
from django.template import Context, loader
from django.http import HttpResponse, Http404, HttpResponseServerError, HttpResponseRedirect, HttpResponsePermanentRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib import auth
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.comments.models import Comment
from django.contrib.sites.models import Site
from django.utils.html import strip_tags
import django.contrib.contenttypes.models as content_type_models
from django.template import RequestContext
from django.core.cache import cache
from django.core.mail import send_mail
from django.contrib.admin.views.decorators import staff_member_required
from django.template.loader import render_to_string
from django.core.urlresolvers import reverse, RegexURLPattern, RegexURLResolver

import sim_pool as sim_pool
import events as events
import glge
from models import *

def index(request): return render_to_response('sim/index.html', {'sim_pool': sim_pool.DEFAULT_SIM_POOL }, context_instance=RequestContext(request))

@staff_member_required
def simulator_pools(request):
	regs = []
	for reg in SimulatorPoolRegistration.objects.all():
		regs.append(reg)
		reg.pool_info = reg.fetch_pool_info(request.session.session_key)
	return render_to_response('sim/simulator_pools.html', { 'simulator_pool_regs':regs }, context_instance=RequestContext(request))

def spaces(request):
	return render_to_response('sim/spaces.html', { 'spaces':Space.objects.all() }, context_instance=RequestContext(request))

def space(request, id):
	space = get_object_or_404(Space, pk=id)
	return render_to_response('sim/space.html', { 'space':space }, context_instance=RequestContext(request))

def thing_app(request, space_id, thing_id):
	space = get_object_or_404(Space, pk=space_id)

	template_module_name = 'template_2' # TODO hard coded for the mo
	module_name = '%s.%s.application' % (os.path.basename(settings.TEMPLATE_APPS_DIR), template_module_name)
	exec 'import %s as app_module' % module_name
	app = app_module.Application()
	resolver = RegexURLResolver(r'^/', app.urlpatterns)
	
	base_path = reverse('sim.views.thing_app', kwargs={ 'space_id':space_id, 'thing_id':thing_id })
	local_path = request.path[len(base_path) - 1:]
	view_function = resolver.resolve(local_path)
	return view_function[0](request)

@staff_member_required
def templates(request):
	return render_to_response('sim/templates.html', { 'templates':Template.objects.all() }, context_instance=RequestContext(request))

@staff_member_required
def template(request, id):
	template = get_object_or_404(Template, pk=id)
	return render_to_response('sim/template.html', { 'template':template }, context_instance=RequestContext(request))

@staff_member_required
def space_debug(request, id):
	space = get_object_or_404(Space, pk=id)
	return render_to_response('sim/space_debug.html', { 'space':space }, context_instance=RequestContext(request))

def spaciblo_js(request):
	return render_to_response('sim/spaciblo.js', {'models':HYDRATE_MODELS, 'scene_graph_classes': glge.SCENE_GRAPH_CLASSES }, context_instance=RequestContext(request), mimetype='application/javascript')

def foo(request):
	return render_to_response('sim/scratch.html', { }, context_instance=RequestContext(request))

def scratch(request):
	if not settings.DEBUG: raise Http404
	return render_to_response('sim/scratch.html', {'sim_pool': sim_pool.DEFAULT_SIM_POOL }, context_instance=RequestContext(request))

def test(request):
	if not settings.DEBUG: raise Http404
	return render_to_response('sim/test.html', { }, context_instance=RequestContext(request))

# Copyright 2010 Trevor F. Smith (http://trevor.smith.name/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
