from vpython import *
from stl import mesh

def stl_compound(filename, vOrigin=vec(0,0,0)):
	obj_mesh = mesh.Mesh.from_file(filename)
	triangles = []

	for i in range(0,len(obj_mesh.vectors)):
		facet = obj_mesh.vectors[i]
		normal = obj_mesh.normals[i]
		v0 = vec(*facet[0])
		v1 = vec(*facet[1])
		v2 = vec(*facet[2])
		vNorm = vec(*normal).hat

		vp_v0 = vertex(pos=v0, normal=vNorm)
		vp_v1 = vertex(pos=v1, normal=vNorm)
		vp_v2 = vertex(pos=v2, normal=vNorm)

		tri = triangle(v0=vp_v0, v1=vp_v1, v2=vp_v2)

		# arr = arrow(pos=(v0+v1+v2)/3, axis=vNorm*0.1, color=color.cyan, shaftwidth=0.005)
		# arr.visible = show_normals
		# normals.append(arr)

		triangles.append(tri)
	return compound(triangles, origin=vOrigin)