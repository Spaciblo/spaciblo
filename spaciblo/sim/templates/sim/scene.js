
//
// GLGE Extensions
//

GLGE.Group.prototype.removeAllChildren = function(){
	while(this.getChildren().length > 0){
		this.removeChild(this.getChildren()[0]);
	}
}
GLGE.Scene.prototype.removeAllChildren = GLGE.Group.prototype.removeAllChildren;

GLGE.Group.prototype.getUserGroup = function(username){
   for(var i=0; i < this.children.length; i++){
      if(username == this.children[i].username) return this.children[i];
      if(typeof this.children[i].getUserGroup != "undefined"){
         var result = this.children[i].getUserGroup(username);
         if(result != null) return result;
      }
   }
   return null;
}

GLGE.Scene.prototype.getUserGroup = GLGE.Group.prototype.getUserGroup;

GLGE.Scene.prototype.getNode = function(uid){
	return GLGE.Assets.get(uid);
}

GLGE.Group.prototype.getNodesByTemplate = function(template_id, results){
	if( (typeof this.group_template != "undefined") && (this.group_template != null) && (template_id == this.group_template.template_id) ){
		results[results.length] = this;
	}
	for(var i=0; i < this.children.length; i++){
		if(typeof this.children[i].getNodesByTemplate != "undefined"){
			this.children[i].getNodesByTemplate(template_id, results);
		}
	}
	return results;
}
GLGE.Scene.prototype.getNodesByTemplate = GLGE.Group.prototype.getNodesByTemplate;

GLGE.Placeable.prototype.setQuatVec=function(q){
	var qc = Spaciblo.Quaternion.normalize(q);
	this.setQuat(qc[0], qc[1], qc[2], qc[3]);
};
GLGE.Placeable.prototype.getQuat=function(){return [this.quatX, this.quatY, this.quatZ, this.quatW];}
GLGE.Placeable.prototype.getRot=function(){return [this.rotX, this.rotY, this.rotZ];}

GLGE.augment(GLGE.Placeable,GLGE.Group);
GLGE.augment(GLGE.Placeable,GLGE.Camera);
