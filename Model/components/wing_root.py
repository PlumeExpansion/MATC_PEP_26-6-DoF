import numpy as np

from typing import TYPE_CHECKING
if TYPE_CHECKING:
	from model_RBird import Model_6DoF
from components.utils import *

class WingRoot:
	def __init__(self, model: 'Model_6DoF', vol_area_data: VolumeAreaData, aero_coeffs: Periodic1D, left):
		self.model = model
		self.vol_area_data = vol_area_data

		self.aero_coeffs = aero_coeffs

		self.left = left
	
	def calc_force_moments(self):
		query = self.model.query.copy()
		if self.left:
			query[2] *= -1
		(self.vol, self.area, self.vol_center, self.area_center) = self.vol_area_data.query(query)
		if self.left:
			self.vol_center[1] *= -1
			self.area_center[1] *= -1
		# buoyant force moment
		self.F_b = self.model.Cb0 @ array([0, 0, -self.model.rho*self.vol*self.model.g])
		self.M_b = cross(self.vol_center, self.F_b)
		# lift & drag force moment
		self.U_mag, self.alpha, self.beta, self.Cbw = stab_frame(self.model.U, self.model.omega, self.area_center, eye3)
		CL_CD = self.aero_coeffs.query(self.alpha*180/pi)
		self.L, self.D, self.F_f, self.M_f = lift_drag(CL_CD[0], CL_CD[1], self.model.rho,
												 self.area, self.U_mag, self.Cbw, self.area_center)
