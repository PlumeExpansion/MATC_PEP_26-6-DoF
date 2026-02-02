import numpy as np

from model_constants import *

r_0 = np.zeros(3)

C0b = np.identity(3)
phi = 0
theta = 0
psi = 0

p = 0
q = 0
r = 0

u = 0
v = 0
w = 0

def update_C0b(phi_i, theta_i, psi_i):
	global C0b
	global phi, theta, psi
	phi = phi_i
	theta = theta_i
	psi = psi_i
	C10 = np.array([
		[cos(psi), sin(psi), 0],
		[-sin(psi), cos(psi), 0],
		[0, 0, 1]
	])
	C21 = np.array([
		[cos(theta), 0, -sin(theta)],
		[0, 1, 0],
		[sin(theta), 0, cos(theta)]
	])
	Cb2 = np.array([
		[1, 0, 0],
		[0, cos(phi), sin(phi)],
		[0, -sin(phi), cos(phi)]
	])
	C0b = np.transpose(Cb2 @ C21 @ C10)
	return C0b