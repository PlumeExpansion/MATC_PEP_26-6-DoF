import numpy as np
from typing import TYPE_CHECKING
if TYPE_CHECKING:
	import model_RBird

from utils import *

class WingRoot:
	def __init__(self, model: 'model_RBird.Model_6DoF', grounded_interp_nd, floating_interp_nd, floating_interp_near, left):
		self.model = model
		self.grounded_interp_nd = grounded_interp_nd
		self.floating_interp_nd = floating_interp_nd
		self.floating_interp_near = floating_interp_near
		self.left = left

		self.C_L0 = self.model.get_const('C_Lwr_0')
		self.C_Lalpha = self.model.get_const('C_Lwr_alpha',True)
		self.C_D0 = self.model.get_const('C_Dwr_0',True)
		self.eff = self.model.get_const('e_wr',True)
		self.AR = self.model.get_const('AR_wr',True)
	
	def calc_force_moment(self):
		query = self.model.query
		if not self.left:
			query = query.copy()
			query[2] *= -1
		grounded = self.grounded_interp_nd(query)
		floating = self.floating_interp_nd(query)
		if np.any(np.isnan(floating)):
			floating = self.floating_interp_near(query)
			print(f"INFO: {'left' if self.left else 'right'} wing root parameters using nearest interpolation - [z, pitch, roll] = {query}")
		self.vol = grounded[0][0]
		self.area = grounded[0][1]
		if self.vol < 1e-6 or self.area < 1e-6:
			return zero3, zero3
		if np.any(np.isnan(grounded)):
			print(f"ERROR: {'left' if self.left else 'right'} wing root parameter interpolation bounds exceeded - [z, pitch, roll] = {query}")
			return zero3, zero3
		self.vol_center = floating[0][0:3]
		self.area_center = floating[0][3:6]
		if not self.left:
			self.vol_center = projYZ @ self.vol_center
			self.area_center = projYZ @ self.area_center
		# buoyant force moment
		self.F_b = self.model.Cb0 * array([0, 0, -self.model.rho*self.vol*self.model.g])
		self.M_b = cross(self.vol_center, self.F_b)
		# lift & drag force moment
		self.U_mag, self.alpha, self.beta, self.Chw = stab_frame(self.model.U, self.model.omega, self.area_center, eye3)
		Q = 1/2*self.model.rho*self.U_mag**2
		self.C_L = self.C_L0 + self.C_Lalpha*self.alpha
		self.C_D = self.C_D0 + self.C_L**2/(pi*self.eff*self.AR)
		self.L = Q*self.C_L*self.area
		self.D = Q*self.C_D*self.area
		self.F_f = self.Chw @ array([-self.D, 0, -self.L])
		self.M_f = cross(self.area_center, self.F_f)
