import numpy as np

from typing import TYPE_CHECKING
if TYPE_CHECKING:
	from model_RBird import Model_6DoF
from components.utils import *

class Panel:
	def __init__(self, model: 'Model_6DoF', id, r_list, aero_coeffs: Periodic1D, rear):
		self.model = model
		self.id = id
		self.r_LE_1 = r_list[0]
		self.r_LE_2 = r_list[1]
		self.r_TE_1 = r_list[2]
		self.r_TE_2 = r_list[3]

		self.aero_coeffs = aero_coeffs
		self.rear = rear

		self.r_qc_1 = 3/4 * self.r_LE_1 + 1/4 * self.r_TE_1
		self.r_qc_2 = 3/4 * self.r_LE_2 + 1/4 * self.r_TE_2

		self.c1 = mag(self.r_LE_1 - self.r_TE_1)
		self.c2 = mag(self.r_LE_2 - self.r_TE_2)

		self.s = mag(projYZ @ (self.r_LE_1 - self.r_LE_2))

		self.gamma = acos(unit(projYZ @ self.r_LE_1 - self.r_LE_2) @ -yHat)
		if self.gamma > pi/2:
			self.gamma -= pi

		self.Cf_ref = array([
			[1, 0, 0],
			[0, cos(self.gamma), sin(self.gamma)],
			[0, -sin(self.gamma), cos(self.gamma)]
		])
		self.Cref_f = np.transpose(self.Cf_ref)

		self.Cfb = self.Cf_ref
		self.Cbf = self.Cref_f
		self.__calc_rot_mats()
		if rear:
			self.to_world = lambda r: self.model.ra_to_world(r)
			self.to_body = lambda r: self.model.ra_to_body(r)
		else:
			self.to_world = lambda r: self.model.body_to_world(r)
			self.to_body = lambda r: r

	def __calc_rot_mats(self):
		if not self.rear: return
		self.Cfb = self.Cf_ref @ self.model.Cra_b
		self.Cbf = transpose(self.Cfb)

	def calc_force_moments(self):
		self.__calc_rot_mats()
		self.__calc_submergence()
		self.U_mag, self.alpha, self.beta, self.Cfw = stab_frame(self.model.U, self.model.omega, self.r_qc_fC_body, self.Cfb)
		CL_CD = self.aero_coeffs.query(self.alpha*180/pi)
		self.L, self.D, self.F_f, self.M_f = lift_drag(CL_CD[0], CL_CD[1], self.model.rho,
												 self.A, self.U_mag, self.Cbf @ self.Cfw, self.r_qc_fC_body)

	def __calc_submergence(self):
		z_qc_1_world = self.to_world(self.r_qc_1)[2]
		z_qc_2_world = self.to_world(self.r_qc_2)[2] 
		self.oneLower = z_qc_1_world > z_qc_2_world
		if self.oneLower:
			temp = z_qc_1_world
			z_qc_1_world = z_qc_2_world
			z_qc_2_world = temp
			r_qc_1 = self.r_qc_2
			r_qc_2 = self.r_qc_1
			c1 = self.c2
			c2 = self.c1
		else:
			r_qc_1 = self.r_qc_1
			r_qc_2 = self.r_qc_2
			c1 = self.c1
			c2 = self.c2
		if (z_qc_2_world - z_qc_1_world <= 1e-6):
			self.f = 1 if z_qc_2_world > 0 else 0
		else:
			self.f = z_qc_2_world / (z_qc_2_world - z_qc_1_world)
			self.f = clip(self.f, 0, 1)
		cf = c2 + (c1-c2)*self.f
		self.A = 1/2*(c1+cf)*self.s*self.f
		sC = self.s*self.f/3*(c2 + 2*cf)/(c2 + cf)
		fC = sC/self.s
		self.r_qc_fC = r_qc_2 + (r_qc_1 - r_qc_2)*fC
		self.r_qc_fC_body = self.to_body(self.r_qc_fC)