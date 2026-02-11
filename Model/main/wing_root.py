import numpy as np
from typing import TYPE_CHECKING
if TYPE_CHECKING:
	import model_RBird

from utils import *

class WingRoot:
	def __init__(self, model: 'model_RBird.Model_6DoF', grounded_interp_nd, floating_interp_nd, floating_interp_near, 
			  aero_coeff, left):
		self.model = model
		self.grounded_interp_nd = grounded_interp_nd
		self.floating_interp_nd = floating_interp_nd
		self.floating_interp_near = floating_interp_near

		alpha = aero_coeff[:,0]
		CL = aero_coeff[:,1]
		CD = aero_coeff[:,2]
		self.CL = lambda alpha_rad: interp(rad2deg(alpha_rad), alpha, CL)
		self.CD = lambda alpha_rad: interp(rad2deg(alpha_rad), alpha, CD)
		self.left = left
	
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
		self.U_mag, self.alpha, self.beta, self.Cbw = stab_frame(self.model.U, self.model.omega, self.area_center, eye3)
		self.L, self.D, self.F_f, self.M_f = lift_drag(self.CL(self.alpha), self.CD(self.alpha), self.model.rho,
												 self.area, self.U_mag, self.Cbw, self.area_center)
