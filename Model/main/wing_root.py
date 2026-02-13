import numpy as np
from typing import TYPE_CHECKING
if TYPE_CHECKING:
	import model_RBird

from utils import *

class WingRoot:
	def __init__(self, model: 'model_RBird.Model_6DoF', rg_interp, aero_coeffs, left):
		self.model = model
		self.rg_interp = rg_interp

		alpha = aero_coeffs[:,0]
		CL = aero_coeffs[:,1]
		CD = aero_coeffs[:,2]
		self.CL = lambda alpha_rad: interp(rad2deg(alpha_rad), alpha, CL)
		self.CD = lambda alpha_rad: interp(rad2deg(alpha_rad), alpha, CD)

		self.left = left
	
	def calc_force_moments(self):
		query = self.model.query.copy()
		if self.left:
			query[2] *= -1
		(self.vol, self.area, self.vol_center, self.area_center) = query_volume_area(self.rg_interp, query)
		if self.left:
			self.vol_center[1] *= -1
			self.area_center[1] *= -1
		# buoyant force moment
		self.F_b = self.model.Cb0 @ array([0, 0, -self.model.rho*self.vol*self.model.g])
		self.M_b = cross(self.vol_center, self.F_b)
		# lift & drag force moment
		self.U_mag, self.alpha, self.beta, self.Cbw = stab_frame(self.model.U, self.model.omega, self.area_center, eye3)
		self.L, self.D, self.F_f, self.M_f = lift_drag(self.CL(self.alpha), self.CD(self.alpha), self.model.rho,
												 self.area, self.U_mag, self.Cbw, self.area_center)
