import numpy as np

from typing import TYPE_CHECKING
if TYPE_CHECKING:
	from model_RBird import Model_6DoF
from utils.utils import *

class WingRoot:
	def __init__(self, model: 'Model_6DoF', vol_area_data, aero_coeffs, left):
		self.model = model
		self.vol_area_data = vol_area_data

		self.aero_coeffs = aero_coeffs

		self.left = left
	
	def calc_force_moments(self):
		(self.vol, self.area, self.vol_center, 
   			self.area_center) = process_volume_area(query_volume_area(self.vol_area_data, 
																calc_query(self.model.query, self.left)), self.left)
		# buoyant force moment
		self.F_b, self.M_b = calc_buoyancy(self.vol, self.model.rho, self.model.g, self.model.Cb0, self.vol_center)
		# lift & drag force moment
		(self.U_mag, self.alpha, self.beta, 
   			self.Cbw, self.L, self.D, self.F_f, self.M_f) = calc_lift_drag(self.model.U, self.model.omega, self.area_center,
																eye3,eye3, self.aero_coeffs, self.model.rho, self.area)

@njit(cache=True)
def calc_query(query, left):
	if left: return query
	mod_query = query.copy()
	mod_query[2] *= -1
	return mod_query

@njit(cache=True)
def process_volume_area(vol_area_query, left):
	if left: return vol_area_query
	vol_area_query[2][1] *= -1
	vol_area_query[3][1] *= -1
	return vol_area_query