import numpy as np
from scipy.optimize import root_scalar
from typing import TYPE_CHECKING
if TYPE_CHECKING:
	import model_RBird

from utils import *

class Hull:
	def __init__(self, model: 'model_RBird.Model_6DoF', rg_interp, hull_aero_coeffs, surf_aero_coeffs):
		self.model = model
		self.rg_interp = rg_interp
		
		alpha_h = hull_aero_coeffs[:,0]
		CL_h = hull_aero_coeffs[:,1]
		CD_h = hull_aero_coeffs[:,2]
		self.CL_h = lambda alpha_rad: interp(rad2deg(alpha_rad), alpha_h, CL_h)
		self.CD_h = lambda alpha_rad: interp(rad2deg(alpha_rad), alpha_h, CD_h)

		alpha_surf = surf_aero_coeffs[:,0]
		CL_surf = surf_aero_coeffs[:,1]
		CD_surf = surf_aero_coeffs[:,2]
		self.CL_surf = lambda alpha_rad: interp(rad2deg(alpha_rad), alpha_surf, CL_surf)
		self.CD_surf = lambda alpha_rad: interp(rad2deg(alpha_rad), alpha_surf, CD_surf)

		self.area_surf = self.model.get_const('A_surf',True)
		self.r_surf = self.model.get_const('r_surf')

		disp0 = self.model.m / self.model.rho
		sol = root_scalar(lambda z: rg_interp(array([z,0,0]))[0][0] - disp0, bracket=[0,0.18], method='brentq')
		if sol.converged:
			z0 = sol.root
			self.area0 = self.rg_interp(array([z0,0,0]))[0][1]
		else:
			raise Exception(f'initial waterline failed to converge - {sol.flag}')
	
	def calc_force_moments(self):
		query = self.model.query.copy()
		query[2] = abs(query[2])
		(self.vol, self.area, self.vol_center, self.area_center) = query_volume_area(self.rg_interp, query)
		# buoyant force moment
		self.F_b = self.model.Cb0 @ array([0, 0, -self.model.rho*self.vol*self.model.g])
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
