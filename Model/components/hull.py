import numpy as np
from scipy.optimize import root_scalar

from typing import TYPE_CHECKING
if TYPE_CHECKING:
	from model_RBird import Model_6DoF
from components.utils import *

class Hull:
	def __init__(self, model: 'Model_6DoF', vol_area_data: VolumeAreaData, hull_aero_coeffs: Periodic1D, surf_aero_coeffs: Periodic1D):
		self.model = model
		self.vol_area_data = vol_area_data
		
		self.hull_aero_coeffs = hull_aero_coeffs

		self.surf_aero_coeffs = surf_aero_coeffs

		self.area_surf = self.model.get_const('A_surf',True)
		self.r_surf = self.model.get_const('r_surf')

		disp0 = self.model.m / self.model.rho
		sol = root_scalar(lambda z: vol_area_data.query(array([z,0,0]))[0] - disp0, bracket=[0,0.18], method='brentq')
		if sol.converged:
			self.z0 = sol.root
			self.area0 = vol_area_data.query(array([self.z0,0,0]))[1]
		else:
			raise Exception(f'initial waterline failed to converge - {sol.flag}')
	
	def calc_force_moments(self):
		query = self.model.query.copy()
		query[2] = abs(query[2])
		(self.vol, self.area, self.vol_center, self.area_center) = self.vol_area_data.query(query)
		# buoyant force moment
		self.F_b = self.model.Cb0 @ array([0, 0, -self.model.rho*self.vol*self.model.g])
		self.M_b = cross(self.vol_center, self.F_b)
		# hull lift & drag force moment
		self.U_mag, self.alpha, self.beta, self.Chw = stab_frame(self.model.U, self.model.omega, self.area_center, eye3)
		CL_CD = self.hull_aero_coeffs.query(self.alpha*180/pi)
		self.L_h, self.D_h, self.F_h, self.M_h = lift_drag(CL_CD[0], CL_CD[1], self.model.rho, 
												 self.area, self.U_mag, self.Chw, self.area_center)
		# combined lift & drag force moment
		self.U_mag_surf, self.alpha_surf, self.beta_surf, self.Chw_surf = stab_frame(self.model.U, self.model.omega, self.r_surf, eye3)
		CL_CD = self.surf_aero_coeffs.query(self.alpha_surf*180/pi)
		(self.L_surf, self.D_surf, 
   		self.F_surf, self.M_surf) = lift_drag(CL_CD[0], CL_CD[1], self.model.rho_surf, 
										   self.area_surf, self.U_mag_surf, self.Chw_surf, self.r_surf)
