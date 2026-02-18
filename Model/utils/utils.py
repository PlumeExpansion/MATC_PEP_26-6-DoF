import numpy as np
import numpy.linalg as LA
from numba import njit
from math import (pi, cos, sin, atan2, asin, acos, sqrt)

from utils.param_utils import *

xHat = np.array([1, 0 ,0])
yHat = np.array([0, 1 ,0])
zHat = np.array([0, 0 ,1])

zero3 = np.zeros(3)
one3 = np.ones(3)
eye3 = np.eye(3)

projYZ = np.array([
	[0, 0, 0],
	[0, 1 ,0],
	[0, 0, 1]
])

flipY = np.array([
	[1, 0, 0],
	[0, -1, 0],
	[0, 0, 1]
])

@njit(cache=True)
def sign(v):
	return -1 if v < 0 else 1

@njit(cache=True)
def unit(vec):
	return vec / mag(vec)

@njit(cache=True)
def mag(vec):
	return sqrt(vec[0]**2 + vec[1]**2 + vec[2]**2)

@njit(cache=True)
def cross(a, b):
	return np.array([
		a[1]*b[2] - a[2]*b[1],
		a[2]*b[0] - a[0]*b[2],
		a[0]*b[1] - a[1]*b[0]
	])

@njit(cache=True)
def stab_frame(U,omega,r_b_frame,C_loc_b):
	U_local = U + cross(omega, r_b_frame)
	U_local_loc_frame = C_loc_b @ U_local
	U_mag = mag(U_local)
	if U_mag < 1e-6:
		return U_mag, U_local_loc_frame, 0.0, 0.0, np.eye(3)
	alpha = atan2(U_local_loc_frame[2], U_local_loc_frame[0])
	beta = asin(U_local_loc_frame[1] / U_mag)
	ca, sa = cos(alpha), sin(alpha)
	cb, sb = cos(beta), sin(beta)
	C_loc_stab = np.array([
		[ca*cb, -ca*sb, -sa],
		[sb, cb, 0.0],
		[sa*cb, -sa*sb, ca]
	])
	return U_mag, U_local_loc_frame, alpha, beta, C_loc_stab

@njit(cache=True)
def calc_lift_drag(U,omega,r_b_frame,C_loc_b,Cb_loc, aero_coeffs, rho,A):
	U_mag, _, alpha, beta, C_loc_stab = stab_frame(U, omega, r_b_frame, C_loc_b)
	CL, CD = query_periodic_1D(aero_coeffs, alpha*180/pi)
	Q = 1/2*rho*U_mag**2
	L = Q*CL*A
	D = Q*CD*A
	Cb_stab = Cb_loc @ C_loc_stab
	F = Cb_stab @ np.array([-D, 0.0, -L])
	M = cross(r_b_frame, F)
	return U_mag, alpha, beta, Cb_stab, C_loc_stab, L, D, F, M

@njit(cache=True)
def calc_buoyancy(vol, rho,g, Cb0,r_body):
	F = Cb0 @ np.array([0.0, 0.0, -rho*vol*g])
	M = cross(r_body, F)
	return F, M

@njit(cache=True)
def ra_to_body(r, Cb_ra, r_ra):
	return r_ra + Cb_ra @ r

@njit(cache=True)
def ra_to_world(r, C0_ra, r_ra_world):
	return C0_ra @ r + r_ra_world

@njit(cache=True)
def body_to_world(r, C0b, r_world):
	return C0b @ r + r_world

@njit(cache=True)
def calc_base_query(C0b, r_CM, r_world, Phi):
	z = body_to_world(-r_CM, C0b, r_world)[2]
	pitch = Phi[1]*180/pi
	roll = Phi[0]*180/pi
	return np.array([z, pitch, roll])

@njit(cache=True)
def calc_base_rot_mats(Phi, psi_ra, r_ra):
	phi = Phi[0]
	theta = Phi[1]
	psi = Phi[2]
	angles = np.array([phi, theta, psi, psi_ra], dtype=np.float64)
	cphi, ctheta, cpsi, cpsi_ra = np.cos(angles)
	sphi, stheta, spsi, spsi_ra = np.sin(angles)
	Cb0 = np.array([
		[cpsi*ctheta, spsi*ctheta, -stheta],
		[cpsi*stheta*sphi - spsi*cphi, spsi*stheta*sphi + cpsi*cphi, ctheta*sphi],
		[cpsi*stheta*cphi + spsi*sphi, spsi*stheta*cphi - cpsi*sphi, ctheta*cphi]
	])
	C0b = np.transpose(Cb0)
	Cb_ra = np.array([
		[cpsi_ra, -spsi_ra, 0.0],
		[spsi_ra, cpsi_ra, 0.0],
		[0.0, 0.0, 1.0]
	])
	Cra_b = np.transpose(Cb_ra)
	C0_ra = C0b @ Cb_ra
	r_ra_world = C0b @ r_ra
	return Cb0, C0b, Cb_ra, Cra_b, C0_ra, r_ra_world

@njit(cache=True)
def calc_H(Phi):
	phi = Phi[0]
	theta = Phi[1]
	cphi, ctheta = cos(phi), cos(theta)
	sphi, stheta = sin(phi), sin(theta)
	ttheta = stheta/ctheta
	return np.array([
		[1.0, sphi*ttheta, cphi*ttheta],
		[0.0, cphi, -sphi],
		[0.0, sphi/ctheta, cphi/ctheta]
	])
