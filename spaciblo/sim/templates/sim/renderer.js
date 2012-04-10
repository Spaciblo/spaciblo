
SpacibloRenderer = {}

//
//
// AssetManager
//
//
//

SpacibloRenderer.AssetManager = function(imageCallback, templateCallback, geometryCallback){
	// This handles loading and unloading asset resources like images and geometry
	var self = this;
	self.imageCallback = imageCallback;
	self.templateCallback = templateCallback;
	self.geometryCallback = geometryCallback;
	self.images = {};
	self.templates = {};
	self.geometries = {};
	
	self.getOrCreateTemplate = function(group_template){
		var template = self.getTemplate(group_template.template_id);
		if(template) return template;
		self.templates[group_template.template_id] = new SpacibloModels.Template(group_template.template_id);
		$.ajax({ 
			type: "GET",
			url: group_template.url,
			dataType: "json",
			success: self.templateLoaded
		});
		return self.templates[group_template.template_id];
	}

	self.updateTemplate = function(template_id, url, key){
		var template = self.getTemplate(template_id);
		if(!template) return;
		$.ajax({ 
			type: "GET",
			url: url,
			dataType: "json",
			success: self.templateLoaded
		});
	}

	self.getTemplate = function(template_id){
		var template = self.templates[template_id];
		if(!template) return null;
		return template;
	}
	
	self.templateLoaded = function(jsonData){
		var template = self.getTemplate(jsonData['id']);
		if(!template){
			console.log("Received template data for an unloaded template: " + jsonData['id']);
			return;
		}
		SpacibloModels.rehydrateModel(jsonData, template);
		template.templateAssets = []
		if(jsonData['assets']){
			for(var i=0; i < jsonData['assets'].length; i++){
				var templateAsset = new SpacibloModels.TemplateAsset();
				SpacibloModels.rehydrateModel(jsonData['assets'][i], templateAsset);
				templateAsset.asset = new SpacibloModels.Asset();
				SpacibloModels.rehydrateModel(jsonData['assets'][i].asset, templateAsset.asset);
				template.templateAssets[i] = templateAsset;
			}
		}
		if (self.templateCallback) self.templateCallback(template);

		// Now that we have notified listeners about the template, load the assets.
		for(var i=0; i < template.templateAssets.length; i++){
			if(template.templateAssets[i].asset.file_type == 'texture'){
				//self.loadImage('/api/sim/template/' + template.id + '/asset/' + template.templateAssets[i].key);
			} else if (template.templateAssets[i].asset.file_type == 'geometry' && !template.templateAssets[i].key.endsWith('.mtl')){
				self.loadGeometry(template.id, template.templateAssets[i].id, '/api/sim/template/' + template.id + '/asset/' + template.templateAssets[i].key);
			} else {
				//console.log('Unknown asset type:', template.templateAssets[i].asset.file_type, template.templateAssets[i])
			}
		}
	}

	self.loadGeometry = function(templateID, templateAssetID, path){
		self.geometries[templateAssetID] = {};
		$.ajax({ 
			type: "GET",
			url: path,
			dataType: "json",
			success: self.geometryLoaded,
			error:self.geometryErrored,
			beforeSend: function(request){ request.templateAssetID = templateAssetID; request.templateID = templateID}
		});
	}

	self.geometryErrored = function(request, status, error){
		if (self.geometryCallback) self.geometryCallback(request.templateID, request.templateAssetID, null);
	}

	self.geometryLoaded = function(jsonData, status, request){
		self.geometries[request.templateAssetID] = jsonData;
		if (self.geometryCallback) self.geometryCallback(request.templateID, request.templateAssetID, self.geometries[request.templateAssetID]);
	}

	self.imageLoaded = function(image, path){
		self.images[path] = {'path':path, 'image':image};
		if(self.imageCallback) self.imageCallback(image, path);
	}

	self.imageErrored = function(path){
		self.images[path] = {'path':path, 'image':null};
		if(self.imageCallback) self.imageCallback(null, path);
	}
	
	self.getImage = function(path){
		var image_info = self.images[path];
		if(image_info) return image_info['image'];
		return null;
	}
	
	self.loadImage = function(path){
		var image = self.getImage(path);
		if(image) return image;
		image = new Image();
		image.onerror = function() { self.imageErrored(path); };
		image.onload = function() {	self.imageLoaded(image, path); };
		image.src = path;
		return null;
	}
}

SpacibloRenderer.DefaultMaterial = new GLGE.Material(GLGE.Assets.createUUID());
SpacibloRenderer.DefaultMaterial.setColor("chocolate");
SpacibloRenderer.DefaultMaterial.setSpecular(1);
SpacibloRenderer.DefaultMaterial.setShininess(20);

// 
//
//
// RENDERABLE
//
//

SpacibloRenderer.Renderable = function(canvas, uid){
	GLGE.Assets.registerAsset(this,uid);
	this.canvas = canvas;
	this.children = [];
	this.group_template = null;
	this.username = null;
}	
GLGE.augment(GLGE.Group,SpacibloRenderer.Renderable);
GLGE.REGISTER_ASSETS=true;

SpacibloRenderer.Renderable.prototype.init = function(nodeJson, templateID){
	this.name = nodeJson.name;
	this.username = nodeJson.username;
	this.group_template = nodeJson.group_template;
	
	this.setLoc(nodeJson.locX, nodeJson.locY, nodeJson.locZ);
	this.setScale(nodeJson.scaleX, nodeJson.scaleY, nodeJson.scaleZ);

	if(nodeJson.mode == GLGE.P_EULER){
		console.log('euler mode!', this, nodeJson);
		this.setRot(nodeJson.rotX, nodeJson.rotY, nodeJson.rotZ);
	} else if(nodeJson.mode == GLGE.P_QUAT){
		this.setQuat(nodeJson.quatX, nodeJson.quatY, nodeJson.quatZ, nodeJson.quatW);
	} else {
		console.log('unknown rot:', nodeJson.mode);
	}
	
	this.setGeometry(nodeJson, templateID);
}

SpacibloRenderer.Renderable.prototype.setGeometry = function(nodeJson, templateID){
	this.removeAllChildren();

	if(nodeJson.mesh != null){
		var node = new GLGE.Object(nodeJson.uid);
		if(nodeJson.material){
			var material = new GLGE.Material(nodeJson.material.uid);
			material.color = {r:1,g:0.5,b:1};//{r:nodeJson.material.color[0], g:nodeJson.material.color[1], b:nodeJson.material.color[2]};
			material.specColor = {r:nodeJson.material.specColor[0], g:nodeJson.material.specColor[1], b:nodeJson.material.specColor[2]};
			material.setShininess(nodeJson.material.shine);
			material.setAlpha(nodeJson.material.alpha);
			if(nodeJson.material.texture){
				if(nodeJson.material.texture.key != null){
					console.log('material', this, nodeJson, nodeJson.material.texture);
					var texture = new GLGE.Texture(nodeJson.material.texture.uid);
					texture.id = nodeJson.material.texture.key;
					texture.setSrc('/api/sim/template/' + templateID + '/asset/' + nodeJson.material.texture.key)
					material.addTexture(texture);
					var layer = new GLGE.MaterialLayer();
					layer.setTexture(material.textures[0]);
					material.addMaterialLayer(layer);
				} else {
					console.log("Ignoring keyless texture", this, nodeJson, nodeJson.material.texture);
				}
			}
			node.setMaterial(material);
		} else {
			node.setMaterial(SpacibloRenderer.DefaultMaterial);
		}

		var mesh = new GLGE.Mesh(nodeJson.mesh.uid);
		mesh.name = nodeJson.mesh.name;
		mesh.setPositions(nodeJson.mesh.positions);
		mesh.setFaces(nodeJson.mesh.faces);
		if(nodeJson.mesh.normals && nodeJson.mesh.normals.length > 0) mesh.setNormals(nodeJson.mesh.normals);
		if(nodeJson.mesh.UV && nodeJson.mesh.UV.length > 0) mesh.setUV(nodeJson.mesh.UV);
		node.setMesh(mesh);
		this.addChild(node);
	}

	if(typeof nodeJson.children == "undefined") return;
	for(var i=0; i < nodeJson.children.length; i++){
		var childRenderable = new SpacibloRenderer.Renderable(self.canvas, nodeJson.children[i].uid);
		childRenderable.init(nodeJson.children[i], templateID);
		this.addChild(childRenderable);
	}
}

SpacibloRenderer.parseArray = function(data){
	var result = [];
	currentArray = data.split(",");
	for(i = 0; i < currentArray.length; i++) result.push(currentArray[i]);
	return result;
}

// 
//
//
// CANVAS
//
//

SpacibloRenderer.Canvas = function(_canvas_id){
	var self = this;
	self.canvas_id = _canvas_id;
	self.username = null;
	self.canvas = null;
	self.glgeRenderer = null;
	self.scene = null;

	self.initialize = function(sceneJson, username) {
		self.username = username;
		self.canvas = document.getElementById(self.canvas_id);		
		if(self.canvas == null) return false;

		self.glgeRenderer = new GLGE.Renderer(self.canvas);

		var light1 = new GLGE.Light(GLGE.Assets.createUUID());
		light1.setLocX(-3);
		light1.setLocY(15)
		light1.setLocZ(7);
		light1.setAttenuationQuadratic(0.00001);
		light1.setAttenuationLinear(0.00000001);
		light1.setAttenuationConstant(1);
		light1.setType(GLGE.L_POINT);

		self.scene = new GLGE.Scene();
		self.scene.obj_name = "I am the scene";
		self.scene.setAmbientColor("#555");
		self.scene.setBackgroundColor("#55F");
		self.scene.addLight(light1);
		self.scene.camera.setLoc(Spaciblo.defaultPosition[0], Spaciblo.defaultPosition[1], Spaciblo.defaultPosition[2]);
		self.scene.camera.setQuat(Spaciblo.defaultRotation[0], Spaciblo.defaultRotation[1], Spaciblo.defaultRotation[2], Spaciblo.defaultRotation[3]);
		for(var i=0; i < sceneJson.children.length; i++){
			var renderable = new SpacibloRenderer.Renderable(self, sceneJson.children[i].uid);
			renderable.init(sceneJson.children[i]);
			self.scene.addChild(renderable);
			if(renderable.username == self.username){
				self.scene.camera.setLoc(renderable.locX, renderable.locY, renderable.locZ);
				self.scene.camera.setQuat(renderable.quatX, renderable.quatY, renderable.quatZ, renderable.quatW);
			}
		}
		self.glgeRenderer.setScene(self.scene);

		self.requestTemplates(self.scene);

	    return true;
	}

	self.requestTemplates = function(node){
		if(node.group_template) self.assetManager.getOrCreateTemplate(node.group_template);
		if(typeof node.children == "undefined") return;
		for(var i=0; i < node.children.length; i++){
			self.requestTemplates(node.children[i]);
		}
	}

	self.render = function() {
		self.glgeRenderer.render();
	}

	self.close = function(){
		if(self.scene){
			self.scene.children = [];
			self.scene.setBackgroundColor("#000");
		}
	}
	
	self.handleImageAsset = function(image, path){ }
	
	self.handleTemplateAsset = function(template){ }
	
	self.handleGeometryAsset = function(templateID, templateAssetID, geometry){
		var nodes = new Array();
		self.scene.getNodesByTemplate(templateID, nodes);
		for(var i=0; i < nodes.length; i++){
			nodes[i].setGeometry(geometry, templateID);
		}
	}

	self.assetManager = new SpacibloRenderer.AssetManager(self.handleImageAsset, self.handleTemplateAsset, self.handleGeometryAsset);
}
