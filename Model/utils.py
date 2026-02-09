import numpy as np
import numpy.linalg as LA
from numpy import (cos, sin, tan, pi, 
				   arccos, arcsin, arctan2, 
				   cross, array, min, max, clip, sign, 
				   eye, zeros, ones, 
				   polyfit, polyval, roots, linspace)

xHat = array([1, 0 ,0])
yHat = array([0, 1 ,0])
zHat = array([0, 0 ,1])

zero3 = zeros(3)
one3 = ones(3)
eye3 = eye(3)

projYZ = array([
	[0, 0, 0],
	[0, 1 ,0],
	[0, 0, 1]
])

flipY = array([
	[1, 0, 0],
	[0, 1, 0],
	[0, 0, 1]
])

def unit(vec):
	return vec / mag(vec)

def mag(vec):
	return LA.norm(vec)

def stab_frame(U, omega, X, C_loc_ref):
	U_local = U + cross(omega, X)
	U_local_loc_frame = C_loc_ref @ U_local
	U_mag = mag(U_local)
	alpha = arctan2(U_local_loc_frame[2], U_local[0])
	beta = arcsin(U_local_loc_frame[1] / U_mag)
	C_loc_stab = array([
		[cos(alpha)*sin(beta), -cos(alpha)*sin(beta), -sin(alpha)],
		[sin(beta), cos(beta), 0],
		[sin(alpha)*cos(beta), -sin(alpha)*sin(beta), cos(alpha)]
	])
	return U_mag, alpha, beta, C_loc_stab