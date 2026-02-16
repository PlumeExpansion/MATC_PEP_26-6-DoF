import numpy as np

from typing import TYPE_CHECKING
if TYPE_CHECKING:
	from model_RBird import Model_6DoF
from utils.utils import *

class Panel:
	def __init__(self, model: 'Model_6DoF', id, r_list, aero_coeffs, rear):
		self.model = model
		self.id = id
		self.r_LE_1 = r_list[0]
		self.r_LE_2 = r_list[1]
		self.r_TE_1 = r_list[2]
		self.r_TE_2 = r_list[3]

		self.aero_coeffs = aero_coeffs
		self.rear = rear

		self.r_qc_1 = 3/4 * self.r_LE_1 + 1/4 * self.r_TE_1
		self.r_qc_2 = 3/4 * self.r_LE_2 + 1/4 * self.r_TE_2

		self.c1 = mag(self.r_LE_1 - self.r_TE_1)
		self.c2 = mag(self.r_LE_2 - self.r_TE_2)

		self.s = mag(projYZ @ (self.r_LE_1 - self.r_LE_2))

		self.gamma = acos(unit(projYZ @ self.r_LE_1 - self.r_LE_2) @ -yHat)
		if self.gamma > pi/2:
			self.gamma -= pi

		self.Cf_ref = np.array([
			[1, 0, 0],
			[0, cos(self.gamma), sin(self.gamma)],
			[0, -sin(self.gamma), cos(self.gamma)]
		])
		self.Cref_f = np.transpose(self.Cf_ref)

	def calc_force_moments(self):
		self.Cfb, self.Cbf = calc_rot_mats(self.rear, self.Cf_ref, self.model.Cra_b)
		(self.one_lower, self.f, self.A, 
   			self.r_qc_fC, self.r_qc_fC_body) = calc_submergence(self.rear, self.r_qc_1, self.r_qc_2, self.model.Cb_ra, self.model.C0_ra,
														 self.model.r_ra, self.model.r_ra_world, self.model.r, self.c1, self.c2, 
														 self.s, self.model.C0b)
		(self.U_mag, self.alpha, self.beta, 
   			self.Cbw, self.Cfw, self.L, self.D, self.F, self.M) = calc_lift_drag(self.model.U, self.model.omega, self.r_qc_fC_body,
																self.Cfb, self.Cbf, self.aero_coeffs, self.model.rho, self.A)

@njit(cache=True)
def calc_rot_mats(rear, Cf_ref, Cra_b):
	if rear:
		Cf_ref = Cf_ref @ Cra_b
	Cref_f = np.transpose(Cf_ref)
	return Cf_ref, Cref_f

# TODO: fix submergence, one lower does not swap properly
@njit(cache=True)
def calc_submergence(rear, r_qc_1,r_qc_2, Cb_ra,C0_ra, r_ra,r_ra_world, r_world, c1,c2,s, C0b):
	if rear:
		z_qc_1_world = ra_to_world(r_qc_1, C0_ra, r_ra_world)[2]
		z_qc_2_world = ra_to_world(r_qc_2, C0_ra, r_ra_world)[2]
	else:
		z_qc_1_world = body_to_world(r_qc_1, C0b, r_world)[2]
		z_qc_2_world = body_to_world(r_qc_2, C0b, r_world)[2]

	one_lower = z_qc_1_world > z_qc_2_world
	if one_lower:
		temp_z = z_qc_1_world
		temp_r_qc = r_qc_1
		temp_c = c1
		z_qc_1_world = z_qc_2_world
		z_qc_2_world = temp_z
		r_qc_1 = r_qc_2
		r_qc_2 = temp_r_qc
		c1 = c2
		c2 = temp_c
	if (z_qc_2_world - z_qc_1_world <= 1e-6):
		f = 1 if z_qc_2_world > 0 else 0
	else:
		f = z_qc_2_world / (z_qc_2_world - z_qc_1_world)
		f = clip(f, 0, 1)
	cf = c2 + (c1-c2)*f
	A = 1/2*(c1+cf)*s*f
	sC = s*f/3*(c2 + 2*cf)/(c2 + cf)
	fC = sC/s
	r_qc_fC = r_qc_2 + (r_qc_1 - r_qc_2)*fC
	r_qc_fC_body = ra_to_body(r_qc_fC, Cb_ra, r_ra) if rear else r_qc_fC
	return one_lower, f, A, r_qc_fC, r_qc_fC_body