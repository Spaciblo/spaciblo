"""A library for manipulating data from Blender."""
import math
import simplejson

from blank_slate.wind.handler import to_json
from spaciblo.sim.glge import Group, Object, Material, Mesh, Texture

def flatten_faces(faces):
	"""Returns a flat array of triples from faces, making two triangles of any quads"""
	result = []
	for face in faces:
		if len(face) == 3:
			result.extend(face)
		elif len(face) == 4:
			result.extend([face[0], face[1], face[2]])
			result.extend([face[2], face[3], face[0]])
		else:
			print("Cannot triangulate faces with length %s" % len(face))
	return result

def flatten_uv(uvs, faces, num_positions):
	"""When passed Returns a 1D array of uv coordinates."""
	two_d_results = [[0.0,0.0] for i in range(num_positions)]
	for i, uv_map in enumerate(uvs):
		for j, uv in enumerate(uv_map):
			two_d_results[faces[i][j]] = uv

	results = []
	for uv in two_d_results: results.extend(uv)
	return results

def flatten(obj_data):
	positions = obj_data['data']['vertices']
	normals = obj_data['data']['normals']
	faces = obj_data['data']['faces']
	if 'uv_map'in obj_data['data'] and len(obj_data['data']['uv_map']) > 0:
		uvs = obj_data['data']['uv_map']
	elif 'uv_tex' in obj_data['data'] and len(obj_data['data']['uv_tex']) > 0:
		uvs = obj_data['data']['uv_tex']
	else:
		uvs = []

	use_normals = len(normals) == len(positions)
	use_uvs = len(uvs) == len(faces)

	decorated_faces = []
	for i, face in enumerate(faces):
		decorated_positions = []
		for j, face_index in enumerate(face):
			pos_index = face_index * 3
			decorated_position = {'position':[positions[pos_index], positions[pos_index + 1], positions[pos_index + 2]]}
			if use_normals:
				normal_index = face_index * 2
				decorated_position['normal'] = [normals[normal_index], normals[normal_index + 1], normals[normal_index + 2]]
			if use_uvs:
				decorated_position['uv'] = uvs[i][j]
			decorated_positions.append(decorated_position)
		if len(decorated_positions) == 3:
			decorated_faces.append(decorated_positions)
		elif len(decorated_positions) == 4:
			# convert a quad into two triangles
			decorated_faces.append([decorated_positions[0], decorated_positions[1], decorated_positions[2]])
			decorated_faces.append([decorated_positions[2], decorated_positions[3], decorated_positions[0]])
		else:
			print('Unhandled face of length %s' % len(decorated_positions))

	positions = []
	normals = []
	uvs = []
	for decorated_face in decorated_faces:
		for decorated_position in decorated_face:
			positions.extend(decorated_position['position'])
			if use_normals: normals.extend(decorated_position['normal'])
			if use_uvs: uvs.extend(decorated_position['uv'])
	triangles = range(len(positions))
	return (positions, normals, triangles, uvs)


class JSONLoader:
	"""Loads the JSON data created by the Blender spaciblo addon."""
	def toGeometry(self, json_string):
		json_data = simplejson.loads(json_string)
		root_group = Group()
		for obj_data in json_data['objects']:
			if obj_data['type'] != 'MESH': continue
			obj = Object()
			obj.name = obj_data['name']
			obj.set_loc(obj_data['location'])
			obj.set_scale(obj_data['scale'])
			if obj_data['rotation_mode'] == ['XYZ']:
				deg = 180 / math.pi;
				deg_rot = [obj_data['rotation_euler'][0] * deg, obj_data['rotation_euler'][1] * deg, -1.0 * obj_data['rotation_euler'][2] * deg]
				obj.set_quat(quat_from_euler(deg_rot))
			else:
				obj.set_quat(obj_data['rotation_quaternion'])
			obj.mesh = Mesh()
			obj.mesh.positions, obj.mesh.normals, obj.mesh.faces, obj.mesh.UV = flatten(obj_data)
			#obj.mesh.positions = obj_data['data']['vertices']
			#obj.mesh.faces = flatten_faces(obj_data['data']['faces'])
			print len(obj.mesh.positions), obj.mesh.positions
			print len(obj.mesh.faces), obj.mesh.faces
			if len(obj_data['data']['materials']) > 0:
				obj.material = self.toMaterial(obj_data['data']['materials'][0])
			else:
				obj.material = Material()
			root_group.children.append(obj)
		return root_group

	def toMaterial(self, matJson):
		material = Material()
		material.name = matJson['name']
		material.color = matJson['diffuse_color']
		material.specColor = matJson['specular_color']
		material.alpha = matJson['alpha']
		if matJson.has_key('active_texture'):
			material.texture = Texture()
			material.texture.name = matJson['active_texture']['name']
			if matJson.has_key('image'):
				material.texture.key = clean_image_key(matJson['image'])
		return material

def clean_image_key(key):
	if key.endswith('.001'): return key[0:-4]
	return key

def make_positive_degree(deg):
	if deg >= 0: return deg
	return deg + 360


def quat_from_euler(vec):
	c = math.pi / 360
	x = make_positive_degree(vec[0]) * c
	y = make_positive_degree(vec[1]) * c
	z = make_positive_degree(vec[2]) * c

	c1 = math.cos(y)
	s1 = math.sin(y)
	c2 = math.cos(-z)
	s2 = math.sin(-z)
	c3 = math.cos(x)
	s3 = math.sin(x)

	c1c2 = c1 * c2
	s1s2 = s1 * s2

	n_w = c1c2 * c3  - s1s2 * s3
  	n_x = c1c2 * s3  + s1s2 * c3
	n_y = s1 * c2 * c3 + c1 * s2 * s3
	n_z = c1 * s2 * c3 - s1 * c2 * s3
	return [n_x, n_y, n_z, n_w]
