import numpy as np
from scipy.optimize import root_scalar
from typing import TYPE_CHECKING
if TYPE_CHECKING:
	import model_RBird

from utils import *

class Hull:
	def __init__(self, model: 'model_RBird.Model_6DoF', grounded_interp_nd, floating_interp_nd, floating_interp_near, 
			  hull_aero_coeff, surf_aero_coeff):
		self.model = model
		self.grounded_interp_nd = grounded_interp_nd
		self.floating_interp_nd = floating_interp_nd
		self.floating_interp_near = floating_interp_near
		
		alpha_h = hull_aero_coeff[:,0]
		CL_h = hull_aero_coeff[:,1]
		CD_h = hull_aero_coeff[:,2]
		self.CL_h = lambda alpha_rad: interp(rad2deg(alpha_rad), alpha_h, CL_h)
		self.CD_h = lambda alpha_rad: interp(rad2deg(alpha_rad), alpha_h, CD_h)

		alpha_surf = hull_aero_coeff[:,0]
		CL_surf = hull_aero_coeff[:,1]
		CD_surf = hull_aero_coeff[:,2]
		self.CL_surf = lambda alpha_rad: interp(rad2deg(alpha_rad), alpha_surf, CL_surf)
		self.CD_surf = lambda alpha_rad: interp(rad2deg(alpha_rad), alpha_surf, CD_surf)

		self.area_surf = self.model.get_const('A_surf',True)
		self.r_surf = self.model.get_const('r_surf')

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
		self.L_h, self.D_h, self.F_h, self.M_h = lift_drag(self.CL_h(self.alpha), self.CD_h(self.alpha), self.model.rho, 
												 self.area, self.U_mag, self.Chw, self.area_center)
		# combined lift & drag force moment
		self.U_mag_surf, self.alpha_surf, self.beta_surf, self.Chw_surf = stab_frame(self.model.U, self.model.omega, self.r_surf, eye3)
		(self.L_surf, self.D_surf, 
   		self.F_surf, self.M_surf) = lift_drag(self.CL_surf(self.alpha_surf), self.CD_surf(self.alpha_surf), 
										   self.model.rho_surf, self.area_surf, self.U_mag_surf, self.Chw_surf, self.r_surf)