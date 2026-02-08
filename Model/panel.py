import numpy as np
import numpy.linalg as LA

from utils import *
import model

class Panel:
	# point locations must be given in body frame
	def __init__(self, model: model.Model_6DoF, r_LE_1, r_LE_2, r_TE_1, r_TE_2, C_L0, C_Lalpha, C_D0, eff, rear):
		self.model = model
		self.r_LE1 = r_LE_1
		self.r_LE2 = r_LE_2
		self.r_TE1 = r_TE_1
		self.r_TE2 = r_TE_2

		self.C_L0 = C_L0
		self.C_Lalpha = C_Lalpha
		self.C_D0 = C_D0
		self.eff = eff
		self.rear = rear

		self.r_qc_1 = 3/4 * r_LE_1 + 1/4 * r_TE_1
		self.r_qc_2 = 3/4 * r_LE_2 + 1/4 * r_TE_2

		self.c1 = mag(r_LE_1 - r_TE_1)
		self.c2 = mag(r_LE_2 - r_TE_2)

		self.s = mag(projYZ @ (r_LE_1 - r_LE_2))

		self.AR = self.s/(self.c1 + self.c2)*2

		self.gamma = arccos(unit(projYZ @ r_LE_1 - r_LE_2) @ -yHat)
		if self.gamma > pi/2:
			self.gamma -= pi

		Cf_ref = array([
			[1, 0, 0],
			[0, cos(self.gamma), sin(self.gamma)],
			[0, -sin(self.gamma), cos(self.gamma)]
		])
		Cref_f = np.transpose(Cf_ref)

		if rear:
			self.get_Cfb = lambda: Cf_ref @ self.model.Cra_b
			self.get_Cbf = lambda: self.model.Cb_ra @ Cref_f
			self.to_world = lambda r: self.model.ra_to_world(r)
			self.to_body = lambda r: self.model.ra_to_body(r)
		else:
			self.get_Cfb = lambda: Cf_ref
			self.get_Cbf = lambda: Cref_f
			self.to_world = lambda r: self.model.body_to_world(r)
			self.to_body = lambda r: r

	# submergence must be called at least once prior
	def calc_force_moment(self, U, omega):
		self.U_mag, self.alpha, self.beta, self.Cfw = stab_frame(U, omega, self.r_qc_fC_body, self.get_Cfb())
		Q = 1/2*self.model.rho*self.U_mag**2 # type: ignore
		C_L = self.C_L0 + self.C_Lalpha*self.alpha
		C_D = self.C_D0 + C_L**2/(pi*self.eff*self.AR)
		L = Q*C_L*self.A
		D = Q*C_D*self.A
		F_f = self.get_Cbf() @ self.Cfw @ array([-D, 0, -L])
		M_f = cross(self.r_qc_fC_body, F_f)
		return F_f, M_f

	def calc_submergence(self):
		self.oneLower = self.to_world(self.r_qc_1)[2] > self.to_world(self.r_qc_2)[2]
		if self.oneLower:
			r_qc_1 = self.r_qc_2
			r_qc_2 = self.r_qc_1
			c1 = self.c2
			c2 = self.c1
		else:
			r_qc_1 = self.r_qc_1
			r_qc_2 = self.r_qc_2
			c1 = self.c1
			c2 = self.c2
		z_qc_1_body = self.to_world(r_qc_1)[2]
		z_qc_2_body = self.to_world(r_qc_2)[2] 
		if (z_qc_2_body - z_qc_1_body <= 1e-6):
			self.f = 1 if z_qc_2_body > 0 else 0
		else:
			self.f = z_qc_2_body / (z_qc_2_body - z_qc_1_body)
			self.f = max([min([self.f, 1]), 0])
		cf = c2 + (c1-c2)*self.f
		self.A = 1/2*(c1+cf)*self.s*self.f
		sC = self.s*self.f/3*(c2 + 2*cf)/(c2 + cf)
		fC = sC/self.s
		self.r_qc_fC = r_qc_2 + (r_qc_1 - r_qc_2)*fC
		self.r_qc_fC_body = self.to_body(self.r_qc_fC)