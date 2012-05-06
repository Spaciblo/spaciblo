//
//
// Models
//
//
SpacibloModels = {}
{% for model in models %}
SpacibloModels.{{ model.type }} = function({% for attr in model.dict %}{{ attr }}{% if not forloop.last %}, {% endif %}{% endfor %}){
	var self = this;
	self.type = '{{ model.type }}';
	{% for attr in model.dict %}self.{{ attr }} = {{ attr }};
	{% endfor %}
	
	self.toJSON = function(){ return Spaciblo.stringify(self); }
}
{% endfor %}

SpacibloModels.rehydrateModel = function(jsonData, model){
	if(!model){
		model_func = null;
		for(var key in SpacibloModels){
			if(key == jsonData['type']){
				model_func = SpacibloModels[key];
				break;
			}
		}
		if(model_func == null){
			console.log('Tried to rehydrate an unknown model: ' + JSON.stringify(jsonData));
			return null;
		}
		model = new model_func();
	}
	for(var key in jsonData) model[key] = jsonData[key];
	return model;
}

SpacibloModels.Template.prototype.update = function(){
	this.has_updated = true;
	var self = this;
	$.ajax({ 
		type: "GET",
		url: this.url,
		dataType: "json",
		success: function(jsonData){ self.handleTemplateLoaded(jsonData); }
	});
}

SpacibloModels.Template.prototype.addListener = function(listener){
	// The listener class must implement geometryUpdated(template)
	if(typeof this.listeners == 'undefined') this.listeners = [];
	this.listeners[this.listeners.length] = listener;
}

SpacibloModels.Template.prototype.removeListener = function(listener){
	if(typeof this.listeners == 'undefined') return;
	for(var i=0; i < this.listeners.length; i++){
		if(listeners[i] == listener){
			listeners.remove(i);
			return;
		}
	}
}

SpacibloModels.Template.prototype.getListeners = function(){
	if(typeof this.listeners == 'undefined') this.listeners = [];
	return this.listeners;	
}

SpacibloModels.Template.prototype.handleTemplateLoaded = function(jsonData){
	SpacibloModels.rehydrateModel(jsonData, this);
	this.templateAssets = []
	if(jsonData['assets']){
		for(var i=0; i < jsonData['assets'].length; i++){
			var templateAsset = new SpacibloModels.TemplateAsset();
			SpacibloModels.rehydrateModel(jsonData['assets'][i], templateAsset);
			templateAsset.asset = new SpacibloModels.Asset();
			SpacibloModels.rehydrateModel(jsonData['assets'][i].asset, templateAsset.asset);
			this.templateAssets[i] = templateAsset;
		}
	}

	for(var i=0; i < this.templateAssets.length; i++){
		if (this.templateAssets[i].asset.file_type == 'geometry' && this.templateAssets[i].key.endsWith('.json')){
			this.requestGeometry(this.templateAssets[i]);
		} else {
			//console.log('Unknown asset type:', template.templateAssets[i].asset.file_type, template.templateAssets[i])
		}
	}
}

SpacibloModels.Template.prototype.requestGeometry = function(templateAsset){
	var self = this;
	$.ajax({ 
		type: "GET",
		url: '/api/sim/template/' + this.id + '/asset/' + templateAsset.key,
		dataType: "json",
		success: self.geometryLoaded,
		error: self.geometryErrored,
		beforeSend: function(request){ request.templateAsset = templateAsset; request.template = self }
	});
}

SpacibloModels.Template.prototype.geometryLoaded = function(jsonData, status, request){
	var templateAsset = request.templateAsset;
	var self = request.template;
	self.geometryJson = jsonData;
	var listeners = self.getListeners();
	for(var i=0; i < listeners.length; i++){
		listeners[i].geometryUpdated(self);
	}
}

SpacibloModels.Template.prototype.geometryErrored = function(request, status, error){
	console.log("Error loading geometry", request, status, error);
}
