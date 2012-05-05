
// If there is no console, ignore console logging
if(!window.console){
    var names = ["log", "debug", "info", "warn", "error", "assert", "dir", "dirxml", "group", "groupEnd", "time", "timeEnd", "count", "trace", "profile", "profileEnd"];
    window.console = {};
    for (var i = 0; i < names.length; ++i){ 
        window.console[names[i]] = function() {}
    }
}

String.prototype.endsWith = function(str){ return (this.match(str+"$")==str) }

{% include "sim/models.js" %}

{% include "sim/input.js" %}

{% include "sim/scene.js" %}

{% include "sim/renderer.js" %}

//
//
// Spaciblo
//
//

Spaciblo = {}

Spaciblo.stringify = function(hydrateObj){
	var data = { 'type': hydrateObj.type }
	for(var key in hydrateObj){
		if(key == 'type' || key == 'toJSON') continue;
		data[key] = hydrateObj[key];
	}
	return JSON.stringify(data);
}


Spaciblo.defaultRotation = [0, 0, 0, 1];
Spaciblo.defaultPosition = [0.0, 0.0, 0.0];

Spaciblo.SpaceClient = function(space_id, canvas) {
	var self = this;
	self.space_id = space_id;
	self.canvas = canvas;
	
	self.username = null;
	self.finished_auth = false;
	self.finished_join = false;
	self.sceneJson = null;
	self.scene = null;

	// set these to receive callbacks on various events
	self.open_handler = function() {}
	self.close_handler = function(){}
	self.authentication_handler = function(successful) {}
	self.join_space_handler = function(successful) {}
	self.add_user_handler = function(successful) {}
	self.user_message_handler = function(username, message) {}
	self.suggest_render_handler = function(){}
	self.close_handler = function(){}

	self.handle_event = function(spaciblo_event) {
		switch(spaciblo_event.type) {
			case 'Heartbeat':
				break;
			case 'UserMoveRequest':
				// TODO stop these from being sent to all clients
				break;
			case 'UserMessage':
				self.user_message_handler(spaciblo_event.username, spaciblo_event.message);
				break;
			case 'AddUserResponse':
				if(spaciblo_event.joined == true){
					self.sceneJson = JSON.parse(spaciblo_event.scene_doc);
				}
				self.finished_join = true;
				self.add_user_handler(spaciblo_event.joined);
				break;
			case 'UserAdded':
				break;
			case 'NodeAdded':
				var nodeJson = JSON.parse(spaciblo_event.json_data);
				if(self.scene.getNode(nodeJson.uid)){
					console.log("Tried to add a duplicate node:", nodeJson.uid);
					break;
				}
				var renderable = new SpacibloRenderer.Renderable(self, nodeJson.uid);
				renderable.init(nodeJson);
				if(nodeJson.username) {
					renderable.username = nodeJson.username;
				}
				if(renderable.username == self.username){
					self.scene.camera.setLoc(renderable.locX, renderable.locY, renderable.locZ);
					self.scene.camera.setQuat(renderable.quatX, renderable.quatY, renderable.quatZ, renderable.quatW);
				}
				self.scene.addChild(renderable);
				self.canvas.requestTemplates(renderable);
				break;
			case 'NodeRemoved':
				var node = self.scene.getNode(spaciblo_event.uid);
				if(node == null){
					console.log("Tried to remove unknown node.", spaciblo_event, spaciblo_event.uid);
					break;
				}
				self.scene.removeChild(node);
				break;
			case 'PlaceableMoved':
				var node = self.scene.getNode(spaciblo_event.uid);
				if(node){
					if(node.username != self.username){
						node.setLocVec(spaciblo_event.location);
						node.setQuatVec(spaciblo_event.quat);
					}
				} else {
					console.log("Tried to move an unknown node: " + spaciblo_event.uid);
				}
				break;
			case 'TemplateUpdated':
				console.log('template updated', spaciblo_event.template_id, spaciblo_event.key, spaciblo_event);
				if(self.canvas) self.canvas.assetManager.updateTemplate(spaciblo_event.template_id, spaciblo_event.url, spaciblo_event.key);
				break;
			default:
				console.log("Received an unknown event: ", spaciblo_event);
		}
	}

	self.wind_client = new Wind.Client();
	self.open = function() {
		self.wind_client.open_handler = self.__open;
		self.wind_client.close_handler = self.__close;
		self.wind_client.app_event_handler = self.handle_event;

		self.wind_client.authentication_handler = function(success){
			if(success){
				self.username = self.wind_client.username;
				self.joinSpace();
			} else {
				console.log('Space client did not authenticate');
			}
		};

		self.wind_client.subscription_handler = function(channel_id, joined, is_member, is_admin, is_editor){
			self.join_space_handler(joined);
		};

		self.wind_client.open();
	}

	self.__open = function(){
		self.open_handler();
	}
	self.__close = function(){
		console.log('Space client closed');
		self.close_handler();
	}
	
	self.sendEvent = function(event){
		self.wind_client.sendEvent(event);
	}

	self.authenticate = function() {
		self.wind_client.authenticate();
	}
	
	self.joinSpace = function() {
		self.sendEvent(new Wind.Events.SubscribeRequest('space_' + self.space_id));
	}
	
	self.addUser = function(location, quat) {
		//if(self.scene.getUserGroup(self.username) != null) return;
		self.sendEvent(new Wind.Events.AddUserRequest(quat, location));
	}
	
	self.sendUserMessage = function(message){
		self.sendEvent(new Wind.Events.UserMessage(self.username, message));
	}

	self.movePlaceable = function(placeable, location, quat){
		self.sendEvent(new Wind.Events.MovePlaceable(quat, placeable.uid, location))
	}
	
	self.close = function() {
		self.wind_client.close();
	}
}

Spaciblo.escapeHTML = function(xml){
	if(xml == null || xml.length == 0){
		return xml;
	}
    return xml.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&apos;");
}

Spaciblo.unescapeHTML = function(xml){
    return xml.replace(/&apos;/g,"'").replace(/&quot;/g,"\"").replace(/&gt;/g,">").replace(/&lt;/g,"<").replace(/&amp;/g,"&");
}

Spaciblo.getSessionCookie = function(){
 return Spaciblo.getCookie('sessionid');
}

Spaciblo.getCookie = function(name) {
    var dc = document.cookie;
    var prefix = name + "=";
    var begin = dc.indexOf("; " + prefix);
    if (begin == -1) {
        begin = dc.indexOf(prefix);
        if (begin != 0) return null;
    } else {
        begin += 2;
    }
    var end = document.cookie.indexOf(";", begin);
    if (end == -1) {
        end = dc.length;
    }
    return Spaciblo.unescapeHTML(dc.substring(begin + prefix.length, end));
}

// sets up all the url parameters in a dictionary
Spaciblo.parseLocationParameters = function(){
    	var paramPhrases = location.search.substring(1, location.search.length).split("&");
    	var paramDict = new Object();
    	for(var i=0; i < paramPhrases.length; i++){
    		paramDict[paramPhrases[i].split("=")[0]] = paramPhrases[i].split("=")[1];
	}
	return paramDict;
}

Spaciblo.locationParameters = Spaciblo.parseLocationParameters();


/**
 * The Quaternion code is derived from Three.js which is licensed under the MIT license: https://github.com/mrdoob/three.js/blob/master/LICENSE
 * Original source here: https://github.com/mrdoob/three.js/blob/master/src/core/Quaternion.js
 * @author mikael emtinger / http://gomo.se/
 * @author alteredq / http://alteredqualia.com/
 * 
 * All quaternions are arrays in the form [x, y, z, w]
 */

Spaciblo.Quaternion = {};

Spaciblo.Quaternion.copy = function(q) {
	var result = [];
	result[0] = q[0];
	result[1] = q[1];
	result[2] = q[2];
	result[3] = q[3];
	return result;
};

Spaciblo.Quaternion.fromEuler = function(vec) {
	var c = Math.PI / 360; // 0.5 * Math.PI / 360, // 0.5 is an optimization
	var x = vec[0] * c;
	var y = vec[1] * c;
	var z = vec[2] * c;

	var c1 = Math.cos( y  ),
		s1 = Math.sin( y  ),
		c2 = Math.cos( -z ),
		s2 = Math.sin( -z ),
		c3 = Math.cos( x  ),
		s3 = Math.sin( x  );

	var c1c2 = c1 * c2,
		s1s2 = s1 * s2;

	var n_w = c1c2 * c3  - s1s2 * s3;
  	var n_x = c1c2 * s3  + s1s2 * c3;
	var n_y = s1 * c2 * c3 + c1 * s2 * s3;
	var n_z = c1 * s2 * c3 - s1 * c2 * s3;
	return [n_x, n_y, n_z, n_w];
};

Spaciblo.Quaternion.fromAxisAngle = function(axis, angle) {
	// axis have to be normalized
	// from http://www.euclideanspace.com/maths/geometry/rotations/conversions/angleToQuaternion/index.htm
	var halfAngle = angle / 2;
	var s = Math.sin( halfAngle );
	n_x = axis[0] * s;
	n_y = axis[1] * s;
	n_z = axis[2] * s;
	n_w = Math.cos( halfAngle );
	return [n_x, n_y, n_z, n_w];
};

Spaciblo.Quaternion.calculateW = function(vec) {
	return -1 * Math.sqrt( Math.abs( 1.0 - vec[0] * vec[0] - vec[1] * vec[1] - vec[2] * vec[2] ) );
};

Spaciblo.Quaternion.inverse = function(q) {
	var result = Spaciblo.Quaternion.copy(q);
	result[0] *= -1;
	result[1] *= -1;
	result[2] *= -1;
	return result;
};

Spaciblo.Quaternion.length = function(q) { return Math.sqrt( q[0] * q[0] + q[1] * q[1] + q[2] * q[2] + q[3] * q[3] ); };

Spaciblo.Quaternion.normalize = function(q) {
	var l = Spaciblo.Quaternion.length(q);
	if (l === 0) return [0,0,0,0]; 

	var qc = Spaciblo.Quaternion.copy(q);
	l = 1 / l;
	qc[0] = qc[0] * l;
	qc[1] = qc[1] * l;
	qc[2] = qc[2] * l;
	qc[3] = qc[3] * l;
	return qc;
};

Spaciblo.Quaternion.multiply = function(q1, q2) {
	// from http://www.euclideanspace.com/maths/algebra/realNormedAlgebra/quaternions/code/index.htm
	var q = []
	q[0] =  q1[0] * q2[3] + q1[1] * q2[2] - q1[2] * q2[1] + q1[3] * q2[0];
	q[1] = -q1[0] * q2[2] + q1[1] * q2[3] + q1[2] * q2[0] + q1[3] * q2[1];
	q[2] =  q1[0] * q2[1] - q1[1] * q2[0] + q1[2] * q2[3] + q1[3] * q2[2];
	q[3] = -q1[0] * q2[0] - q1[1] * q2[1] - q1[2] * q2[2] + q1[3] * q2[3];
	return q;
};

Spaciblo.Quaternion.multiplyVector3 = function (q, vec) {
	var dest = [0,0,0];

	var x = vec[0];
	var y = vec[1];
	var z = vec[2];
	var qx = q[0];
	var qy = q[1];
	var qz = q[2]
	var qw = q[3];

	// calculate quat * vec
	var ix =  qw * x + qy * z - qz * y,
		iy =  qw * y + qz * x - qx * z,
		iz =  qw * z + qx * y - qy * x,
		iw = -qx * x - qy * y - qz * z;

	// calculate result * inverse quat
	dest[0] = ix * qw + iw * -qx + iy * -qz - iz * -qy;
	dest[1] = iy * qw + iw * -qy + iz * -qx - ix * -qz;
	dest[2] = iz * qw + iw * -qz + ix * -qy - iy * -qx;

	return dest;
};

Spaciblo.Quaternion.slerp = function ( qa, qb, qm, t ) {
	// http://www.euclideanspace.com/maths/algebra/realNormedAlgebra/quaternions/slerp/
	var cosHalfTheta = qa[3] * qb[3] + qa[0] * qb[0] + qa[1] * qb[1] + qa[2] * qb[2];

	if (cosHalfTheta < 0) {
		qm[3] = -qb[3]; qm[0] = -qb[0]; qm[1] = -qb[1]; qm[2] = -qb[2];
		cosHalfTheta = -cosHalfTheta;
	} else {
		qm = Spaciblo.Quaternion.copy(qb);
	}

	if ( Math.abs( cosHalfTheta ) >= 1.0 ) {
		qm[3] = qa[3]; qm[0] = qa[0]; qm[1] = qa[1]; qm[2] = qa[2];
		return qm;
	}

	var halfTheta = Math.acos( cosHalfTheta ),
	sinHalfTheta = Math.sqrt( 1.0 - cosHalfTheta * cosHalfTheta );

	if ( Math.abs( sinHalfTheta ) < 0.001 ) {
		qm[3] = 0.5 * ( qa[3] + qb[3] );
		qm[0] = 0.5 * ( qa[0] + qb[0] );
		qm[1] = 0.5 * ( qa[1] + qb[1] );
		qm[2] = 0.5 * ( qa[2] + qb[2] );
		return qm;
	}

	var ratioA = Math.sin( ( 1 - t ) * halfTheta ) / sinHalfTheta,
	ratioB = Math.sin( t * halfTheta ) / sinHalfTheta;

	qm[3] = ( qa[3] * ratioA + qm[3] * ratioB );
	qm[0] = ( qa[0] * ratioA + qm[0] * ratioB );
	qm[1] = ( qa[1] * ratioA + qm[1] * ratioB );
	qm[2] = ( qa[2] * ratioA + qm[2] * ratioB );

	return qm;
}

Spaciblo.Quaternion.brokenToEuler = function(quat){
	// This isn't right.  Don't use it.  Perhaps it's wrong handed?
	var w2 = quat[3] * quat[3];
	var x2 = quat[0] * quat[0];
	var y2 = quat[1] * quat[1];
	var z2 = quat[2] * quat[2];
	var unitLength = w2 + x2 + y2 + z2;    // Normalised == 1, otherwise correction divisor.
	var abcd = quat[3] * quat[0] + quat[1] * quat[2];
	var eps = 1e-7;    // TODO: pick from your math lib instead of hardcoding.
	var pi = Math.PI;
	var yaw, pitch, roll;
	if (abcd > (0.5-eps) * unitLength){
		yaw = 2 * Math.atan2(quat[1], quat[3]);
		pitch = pi;
		roll = 0;
	} else if (abcd < (-0.5 + eps) * unitLength) {
		yaw = -2 * Math.atan2(quat[1], quat[3]);
		pitch = -pi;
		roll = 0;
	} else {
		var adbc = quat[3] * quat[2] - quat[0]*quat[1];
		var acbd = quat[3] * quat[1] - quat[0]*quat[2];
		yaw = Math.atan2(2 * adbc, 1 - 2 * (z2 + x2));
		pitch = Math.asin(2 * abcd / unitLength);
		roll = Math.atan2(2 * acbd, 1 - 2 * (y2 + x2));
	}
	var deg = 180 / Math.PI;
	return [pitch * deg, roll * deg, yaw * deg]
}
