import numpy as np

from typing import TYPE_CHECKING
if TYPE_CHECKING:
	from model_RBird import Model_6DoF
from utils.utils import *

class Propulsor:
	def __init__(self, model: 'Model_6DoF', prop_data):
		self.model = model

		self.d = self.model.get_const('d')

		self.eta_T = self.model.get_const('eta_T',True)
		self.eta_T_surf = self.model.get_const('eta_T_surf',True)
		
		self.w_fs = self.model.get_const('w_fs',True)
		self.w_f = self.model.get_const('w_f',True)

		self.r_prop = self.model.get_const('r_prop_ra')
		self.r_d_1 = self.r_prop - self.d/2*zHat
		self.r_d_2 = self.r_prop + self.d/2*zHat

		self.prop_data = prop_data

		# default inputs
		self.V = 0

	def get_input(self):
		return self.V
	def set_input(self, input):
		self.V = input

	def calc_force_moments(self):
		_, U_p, _,_, self.Cra_w = stab_frame(self.model.U, self.model.omega, 
									   ra_to_body(self.r_prop, self.model.Cb_ra, self.model.r_ra), self.model.Cra_b)
		u_p = U_p[0]
		self.w = self.w_f + (self.w_fs + self.w_f)*self.model.hull.area/self.model.hull.area0
		self.vA = u_p*(1-self.w)
		z_d_2_world = ra_to_world(self.r_d_2, self.model.C0_ra, self.model.r_ra_world)[2]
		z_d_1_world = ra_to_world(self.r_d_1, self.model.C0_ra, self.model.r_ra_world)[2]
		(self.fp, self.n, self.T, self.Q, self.I, self.F, self.M) = calc_force_moment(z_d_2_world, z_d_1_world,
												  self.model.rho_surf, self.model.rho, self.vA, self.V, self.prop_data, 
												  self.eta_T, self.eta_T_surf, self.model.Cb_ra, self.r_prop)

@njit(cache=True)
def calc_force_moment(z_d_2_world, z_d_1_world, rho_surf,rho, vA,V, prop_data,eta_T,eta_T_surf, Cb_ra, r_prop_body):
	fp = z_d_2_world / (z_d_2_world - z_d_1_world)
	fp = clip(fp, 0, 1)
	rho = rho_surf + (rho - rho_surf)*fp
	eta_T = eta_T_surf + (eta_T - eta_T_surf)*fp

	n,T,Q,I = trilinear_interp(prop_data, np.array([rho, vA, V]))
	F = Cb_ra @ np.array([eta_T*T, 0, 0])
	M = cross(r_prop_body, F)
	return fp, n, T, Q, I, F, M