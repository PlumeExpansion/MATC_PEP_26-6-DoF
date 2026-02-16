import numpy as np
from scipy.optimize import root_scalar

from typing import TYPE_CHECKING
if TYPE_CHECKING:
	from model_RBird import Model_6DoF
from utils.utils import *

class Hull:
	def __init__(self, model: 'Model_6DoF', vol_area_data, hull_aero_coeffs, surf_aero_coeffs):
		self.model = model
		
		self.vol_area_data = vol_area_data
		self.hull_aero_coeffs = hull_aero_coeffs
		self.surf_aero_coeffs = surf_aero_coeffs

		self.area_surf = self.model.get_const('A_surf',True)
		self.r_surf = self.model.get_const('r_surf')

		disp0 = self.model.m / self.model.rho
		sol = root_scalar(lambda z: query_volume_area(vol_area_data, np.array([z,0,0]))[0] - disp0, bracket=[0,0.2], method='brentq')
		if sol.converged:
			self.z0 = sol.root
			self.area0 = query_volume_area(vol_area_data, np.array([self.z0,0,0]))[1]
		else:
			raise Exception(f'initial waterline failed to converge - {sol.flag}')
	
	def calc_force_moments(self):
		(self.vol, self.area, self.vol_center, self.area_center) = query_volume_area(self.vol_area_data, calc_query(self.model.query))
		# buoyant force moment
		self.F_b, self.M_b = calc_buoyancy(self.vol, self.model.rho, self.model.g, self.model.Cb0, self.vol_center)
		# hull lift & drag force moment
		(self.U_mag, self.alpha, self.beta, 
   			_, self.Cbw, self.L_h, self.D_h, self.F_h, self.M_h) = calc_lift_drag(self.model.U, self.model.omega, self.area_center,
																eye3,eye3, self.hull_aero_coeffs, self.model.rho, self.area)
		# surfaced lift & drag force moment
		(self.U_mag_surf, self.alpha_surf, self.beta_surf, _, self.Cbw_surf, 
   			self.L_surf, self.D_surf, self.F_surf, self.M_surf) = calc_lift_drag(self.model.U, self.model.omega, self.r_surf,
																eye3,eye3, self.surf_aero_coeffs, self.model.rho_surf, self.area_surf)

@njit(cache=True)
def calc_query(query):
	mod_query = query.copy()
	mod_query[2] = abs(query[2])
	return mod_query