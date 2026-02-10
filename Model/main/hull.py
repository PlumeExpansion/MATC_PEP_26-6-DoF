import numpy as np
from scipy.optimize import root_scalar
from typing import TYPE_CHECKING
if TYPE_CHECKING:
	import model_RBird

from utils import *

class Hull:
	def __init__(self, model: 'model_RBird.Model_6DoF', grounded_interp_nd, floating_interp_nd, floating_interp_near):
		self.model = model
		self.grounded_interp_nd = grounded_interp_nd
		self.floating_interp_nd = floating_interp_nd
		self.floating_interp_near = floating_interp_near
		
		self.C_L0 = self.model.get_const('C_Lh_0')
		self.C_Lalpha = self.model.get_const('C_Lh_alpha',True)
		self.C_D0 = self.model.get_const('C_Dh_0',True)
		self.eff = self.model.get_const('e_h',True)

		self.C_Lc_0 = self.model.get_const('C_Lc_0')
		self.C_Lc_alpha = self.model.get_const('C_Lc_alpha',True)
		self.C_Dc_0 = self.model.get_const('C_Dc_0',True)
		self.C_Dc_alpha2 = self.model.get_const('C_Dc_alpha2',True)

		self.beam = self.model.get_const('B',True)
		self.L_PP = self.model.get_const('L_PP',True)
		
		self.L_PP = self.model.get_const('L_PP',True)
		self.area_surf = self.model.get_const('A_surf',True)
		self.r_surf = self.model.get_const('r_surf')

		self.AR = self.beam / self.L_PP

		disp0 = self.model.m / self.model.rho
		sol = root_scalar(lambda z: grounded_interp_nd(array([z,0,0]))[0][0] - disp0, bracket=[0,0.18], method='brentq')
		if sol.converged:
			z0 = sol.root
			self.area0 = self.grounded_interp_nd(array([z0,0,0]))[0][1]
		else:
			self.model.init_errors += 1
			print(f'ERROR: initial waterline height failed to converge, termination flag: {sol.flag}')

	def calc_force_moment(self):
		grounded = self.grounded_interp_nd(self.model.query)
		floating = self.floating_interp_nd(self.model.query)
		if np.any(np.isnan(floating)):
			floating = self.floating_interp_near(self.model.query)
			print(f"INFO: hull parameters using nearest interpolation - [z, pitch, roll] = {self.model.query}")
		self.vol = grounded[0][0]
		self.area = grounded[0][1]
		if self.vol < 1e-6 or self.area < 1e-6:
			return zero3, zero3
		if np.any(np.isnan(grounded)):
			print(f"ERROR: hull parameter interpolation bounds exceeded - [z, pitch, roll] = {self.model.query}")
			return zero3, zero3
		self.vol_center = floating[0][0:3]
		self.area_center = floating[0][3:6]
		# buoyant force moment
		self.F_b = self.model.Cb0 * array([0, 0, -self.model.rho*self.vol*self.model.g])
		self.M_b = cross(self.vol_center, self.F_b)
		# hull lift & drag force moment
		self.U_mag, self.alpha, self.beta, self.Chw = stab_frame(self.model.U, self.model.omega, self.area_center, eye3)
		Q = 1/2*self.model.rho*self.U_mag**2
		self.C_L = self.C_L0 + self.C_Lalpha*self.alpha
		self.C_D = self.C_D0 + self.C_L**2/(pi*self.eff*self.AR)
		self.L = Q*self.C_L*self.area
		self.D = Q*self.C_D*self.area
		self.F_h = self.Chw @ array([-self.D, 0, -self.L])
		self.M_h = cross(self.area_center, self.F_h)
		# combined lift & drag force moment
		self.c_U_mag, self.c_alpha, self.c_beta, self.c_Chw = stab_frame(self.model.U, self.model.omega, self.r_surf, eye3)
		Q = 1/2*self.model.rho_surf*self.c_U_mag**2
		self.C_L_c = self.C_Lc_0 + self.C_Lc_alpha*self.c_alpha
		self.C_D_c = self.C_Dc_0 + self.C_Dc_alpha2*self.c_alpha**2
		self.L_c = Q*self.C_L_c*self.area_surf
		self.D_c = Q*self.C_D_c*self.area_surf
		self.F_c = self.c_Chw @ array([-self.D_c, 0, -self.L_c])
		self.M_c = cross(self.r_surf, self.F_c)