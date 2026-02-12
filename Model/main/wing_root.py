import numpy as np
from typing import TYPE_CHECKING
if TYPE_CHECKING:
	import model_RBird

from utils import *

class WingRoot:
	def __init__(self, model: 'model_RBird.Model_6DoF', g_linear, f_linear, f_nearest, aero_coeffs, left):
		self.model = model
		self.g_linear = g_linear
		self.f_linear = f_linear
		self.f_nearest = f_nearest

		alpha = aero_coeffs[:,0]
		CL = aero_coeffs[:,1]
		CD = aero_coeffs[:,2]
		self.CL = lambda alpha_rad: interp(rad2deg(alpha_rad), alpha, CL)
		self.CD = lambda alpha_rad: interp(rad2deg(alpha_rad), alpha, CD)
		self.source = f'{"left" if left else "right"} wing root'
	
	def calc_force_moments(self):
		(self.vol, self.area, self.vol_center, self.area_center) = query_volume_area(self.g_linear, self.f_linear, 
																			   self.f_nearest, self.model.query, self.source)
		# buoyant force moment
		self.F_b = self.model.Cb0 @ array([0, 0, -self.model.rho*self.vol*self.model.g])
		self.M_b = cross(self.vol_center, self.F_b)
		# lift & drag force moment
		self.U_mag, self.alpha, self.beta, self.Cbw = stab_frame(self.model.U, self.model.omega, self.area_center, eye3)
		self.L, self.D, self.F_f, self.M_f = lift_drag(self.CL(self.alpha), self.CD(self.alpha), self.model.rho,
												 self.area, self.U_mag, self.Cbw, self.area_center)
