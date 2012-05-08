
//
//
// SpacibloInput
//
//
//

SpacibloInput = {}

SpacibloInput.InputManager = function(_space_client){
	var self = this;
	self.space_client = _space_client;
	self.user_node = null;
	self.x_delta = 1;
	self.y_delta = 1;
	self.z_delta = 1;
	self.y_rot_delta = Math.PI / 24.0;
	
	self.mouse = new GLGE.MouseInput(space_client.canvas.canvas);
	self.mouseovercanvas = false;
	self.key_event = null;
 	self.now = parseInt(new Date().getTime());
	self.lastTime = parseInt(new Date().getTime());

	self.walkHeight = 1.0;
	self.maxFallPerMove = 100.0;

	space_client.canvas.canvas.onmouseover=function(e){ self.mouseovercanvas=true; }
	space_client.canvas.canvas.onmouseout=function(e){ self.mouseovercanvas=false; }

	self.getUserNode = function(){
		if(self.user_node == null){
			self.user_node = self.space_client.canvas.scene.getUserGroup(self.space_client.username);
		}
		return self.user_node;
	}
	
	self.relativeMove = function(x, y, z, userNode){
		var rotatedVec = Spaciblo.Quaternion.multiplyVector3(userNode.getQuat(), [x, y, z]);
		var newLoc = [userNode.locX + rotatedVec[0], userNode.locY + rotatedVec[1], userNode.locZ + rotatedVec[2]];
		var rayResult = self.space_client.scene.ray(newLoc, [0.0, Math.PI, 0.0]);
		if(rayResult && rayResult.distance <= self.maxFallPerMove){
			if(rayResult.distance < self.walkHeight){
				newLoc[1] += self.walkHeight - rayResult.distance;
			} else if (rayResult.distance > self.walkHeight){
				newLoc[1] -= rayResult.distance - self.walkHeight;
			}
		}
		userNode.setLocVec(newLoc);
		self.space_client.scene.camera.setLoc(userNode.locX, userNode.locY, userNode.locZ);
	}
	
	self.relativeRot = function(axis, angle, userNode){
		var quat = Spaciblo.Quaternion.multiply(userNode.getQuat(), Spaciblo.Quaternion.fromAxisAngle(axis, angle));
		userNode.setQuatVec(quat);
		self.space_client.scene.camera.setQuatVec(quat);
	}

	self.add_event_source = function(node){
		$(node).keydown(self.handle_keydown).keyup(self.handle_keyup);
	}

	self.handle_keydown = function(event){
		// This is the browser callback for key events which happen outside of the render loop
		// The only thing it should do is assign the event to self.key_event
		self.key_event = event;
	}

	self.handle_keyup = function(event){
		// This returns false so that the event doesn't trickle down
		return false;
	}

	self.handle_keys = function(){
		// This is the function which is called during the render loop to handle any key events which have come in since the last render
		var event = self.key_event;
		if(event == null) return;
		self.key_event = null;

		if(event.ctrlKey) return true;
		if(event.metaKey) return true;
		var userNode = self.getUserNode();
		if(userNode == null){
			console.log('No user thing');
			return;
		}
		switch(event.keyCode){
			case 37: //left arrow
			case 65: //a key
				self.relativeMove(-self.x_delta, 0, 0, userNode);
				break;
			case 39: //right
			case 68: //d key
				self.relativeMove(self.x_delta, 0, 0, userNode);
				break;
			case 38: //up arrow
			case 87: //w key
				self.relativeMove(0, 0, -self.z_delta, userNode);
				break;
			case 40: //down
			case 83: //s key
				self.relativeMove(0, 0, self.z_delta, userNode);
				break;
			case 82: //r key
				self.relativeMove(0, self.y_delta, 0, userNode);
				break;
			case 70: //f key
				self.relativeMove(0, -self.y_delta, 0, userNode);
				break;
			case 81: //q key
				self.relativeRot([0, 1, 0], self.y_rot_delta, userNode);
				break;
			case 69: //e key
				self.relativeRot([0, 1, 0], -1 * self.y_rot_delta, userNode);
				break;
			default:
				return;
		}

		var event = new Wind.Events.UserMoveRequest(self.space_client.username, [userNode.quatX, userNode.quatY, userNode.quatZ, userNode.quatW], [userNode.locX, userNode.locY, userNode.locZ]);
		self.space_client.sendEvent(event);
	}

	self.reset_location = function(){
		var userNode = self.getUserNode();
		if(userNode == null){
			console.log('No user thing');
			return;
		}
		self.space_client.scene.camera.setLoc(Spaciblo.defaultPosition[0], Spaciblo.defaultPosition[1], Spaciblo.defaultPosition[2]);
		self.space_client.scene.camera.setQuat(Spaciblo.defaultRotation[0], Spaciblo.defaultRotation[1], Spaciblo.defaultRotation[2], Spaciblo.defaultRotation[3]);
		userNode.setLoc(Spaciblo.defaultPosition[0], Spaciblo.defaultPosition[1], Spaciblo.defaultPosition[2]);
		userNode.setQuat(Spaciblo.defaultRotation[0], Spaciblo.defaultRotation[1], Spaciblo.defaultRotation[2], Spaciblo.defaultRotation[3]);
		var event = new Wind.Events.UserMoveRequest(self.space_client.username, [userNode.quatX, userNode.quatY, userNode.quatZ, userNode.quatW], [userNode.locX, userNode.locY, userNode.locZ]);
		self.space_client.sendEvent(event);
	}

	self.mouse_look = function(){
		self.now = parseInt(new Date().getTime());
		if(self.mouseovercanvas){
			var canvasElement = space_client.canvas.canvas;
			var mousepos = self.mouse.getMousePosition();
			mousepos.x = mousepos.x - canvasElement.offsetLeft;
			mousepos.y = mousepos.y - canvasElement.offsetTop;

			var inc = (mousepos.y - (canvasElement.offsetHeight / 2)) / 500;
			var trans = GLGE.mulMat4Vec4(self.space_client.scene.camera.getRotMatrix(), [0,0,-1,1]);
			var mag = Math.pow(Math.pow(trans[0],2) + Math.pow(trans[1],2), 0.5);

			trans[0] = trans[0] / mag;
			trans[1] = trans[1] / mag;

			var width = canvasElement.offsetWidth;
			if(mousepos.x < width*0.3){
				var turn = Math.pow((mousepos.x-width*0.3)/(width*0.3),2)*0.005*(self.now-self.lastTime);
				self.relativeRot([0, 1, 0], turn, self.getUserNode());
			}
			if(mousepos.x > width*0.7){
				var turn = Math.pow((mousepos.x-width*0.7)/(width*0.3),2)*0.005*(self.now-self.lastTime);
				self.relativeRot([0, 1, 0], -turn, self.getUserNode());
			}
		}
		self.lastTime = self.now;
	}
}
