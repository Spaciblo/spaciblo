
SpacibloRenderer = {}

//
//
// AssetManager
//
//
//

SpacibloRenderer.AssetManager = function(){
	// This keeps track of templates
	var self = this;
	self.templates = {};
	
	self.getTemplate = function(template_id){
		// Return the Template iff it exists, otherwise null
		var template = self.templates[template_id];
		if(!template) return null;
		return template;
	}
	
	self.getOrCreateTemplate = function(group_template){
		// Return the Template, creating if necessary
		var template = self.getTemplate(group_template.template_id);
		if(template) return template;
		self.templates[group_template.template_id] = new SpacibloModels.Template(group_template.template_id);
		self.templates[group_template.template_id].url = group_template.url;
		return self.templates[group_template.template_id];
	}

	self.updateAllTemplates = function(){
		for(var templateID in self.templates){
			self.templates[templateID].update();
		}
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

SpacibloRenderer.Renderable.prototype.init = function(nodeJson, template){
	this.name = nodeJson.name;
	this.template = template;
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
}

SpacibloRenderer.Renderable.prototype.geometryUpdated = function(template){
	this.setGeometry(template.geometryJson, template);
}

SpacibloRenderer.Renderable.prototype.setGeometry = function(nodeJson, template){
	this.removeAllChildren();
	if(nodeJson.mesh != null){
		var node = new GLGE.Object(nodeJson.uid);
		if(nodeJson.material){
			var material = new GLGE.Material(nodeJson.material.uid);
			material.color = {r:nodeJson.material.color[0], g:nodeJson.material.color[1], b:nodeJson.material.color[2]};
			material.specColor = {r:nodeJson.material.specColor[0], g:nodeJson.material.specColor[1], b:nodeJson.material.specColor[2]};
			material.setShininess(nodeJson.material.shine);
			material.setAlpha(nodeJson.material.alpha);
			if(nodeJson.material.texture){
				if(nodeJson.material.texture.key != null){
					var texture = new GLGE.Texture(nodeJson.material.texture.uid);
					texture.id = nodeJson.material.texture.key;
					texture.setSrc('/api/sim/template/' + template.id + '/asset/' + nodeJson.material.texture.key)
					material.addTexture(texture);
					var layer = new GLGE.MaterialLayer();
					layer.setTexture(material.textures[0]);
					material.addMaterialLayer(layer);
				} else {
					console.log("Ignoring keyless texture", this, nodeJson, template.id, nodeJson.material.texture);
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
		childRenderable.init(nodeJson.children[i], template);
		childRenderable.setGeometry(nodeJson.children[i], template);
		this.addChild(childRenderable);
	}
	if(this.username != null){
		// The body can't be pickable because otherwise our motion picker would pick it when moving backwards.
		this.setPickable(false);
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

window.globalNoWebGLError = 'Do not show'; //Prevent GLGE from showing an error window

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

		try {
			self.glgeRenderer = new GLGE.Renderer(self.canvas);
			self.scene = new GLGE.Scene();
		} catch(err) {
			console.log("Error:", err, this);
			return false;
		}

		self.scene.fogType = sceneJson.fogType;
		self.scene.fogNear = sceneJson.forNear;
		self.scene.fogFar = sceneJson.fogFar;

		self.scene.obj_name = "I am the scene";
		self.scene.backgroundColor = {
			'r':sceneJson.backgroundColor[0],
			'g':sceneJson.backgroundColor[1],
			'b':sceneJson.backgroundColor[2],
			'a':sceneJson.backgroundColor[3]
		};

		self.scene.ambientColor = {
			'r':sceneJson.ambientColor[0],
			'g':sceneJson.ambientColor[1],
			'b':sceneJson.ambientColor[2]
		};

		self.scene.camera.setLoc(Spaciblo.defaultPosition[0], Spaciblo.defaultPosition[1], Spaciblo.defaultPosition[2]);
		self.scene.camera.setQuat(Spaciblo.defaultRotation[0], Spaciblo.defaultRotation[1], Spaciblo.defaultRotation[2], Spaciblo.defaultRotation[3]);
		for(var i=0; i < sceneJson.children.length; i++){
			if(typeof sceneJson.children[i].softness != 'undefined'){
				// Make a light
				var light = new GLGE.Light(GLGE.Assets.createUUID());
				for(var key in sceneJson.children[i]){
					light[key] = sceneJson.children[i][key];
				}
				light.color = {
					'r':sceneJson.children[i].color[0],
					'g':sceneJson.children[i].color[1],
					'b':sceneJson.children[i].color[2],
				};
				self.scene.addLight(light);
				continue;
			}

			var renderable = new SpacibloRenderer.Renderable(self, sceneJson.children[i].uid);
			var template = self.assetManager.getOrCreateTemplate(sceneJson.children[i].group_template);
			renderable.init(sceneJson.children[i], template);
			template.addListener(renderable);
			self.scene.addChild(renderable);
			if(renderable.username == self.username){
				self.scene.camera.setLoc(renderable.locX, renderable.locY, renderable.locZ);
				self.scene.camera.setQuat(renderable.quatX, renderable.quatY, renderable.quatZ, renderable.quatW);
			}
		}
		self.glgeRenderer.setScene(self.scene);
		self.assetManager.updateAllTemplates();
	    return true;
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

	self.assetManager = new SpacibloRenderer.AssetManager(self.handleImageAsset, self.handleTemplateAsset, self.handleGeometryAsset);
}
