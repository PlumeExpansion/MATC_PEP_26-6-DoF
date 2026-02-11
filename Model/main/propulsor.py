import numpy as np
from typing import TYPE_CHECKING
if TYPE_CHECKING:
	import model_RBird

from utils import *

class Propulsor:
	def __init__(self, model: 'model_RBird.Model_6DoF', thrust_torque_coeffs):
		self.model = model

		self.d = self.model.get_const('d',True)

		self.eta_T = self.model.get_const('eta_T',True)
		
		self.w_fs = self.model.get_const('w_fs',True)
		self.w_f = self.model.get_const('w_f',True)

		KV = self.model.get_const('KV',True)
		self.Kt = self.model.get_const('Kt',True)
		I0 = self.model.get_const('I0',True)
		RPM0 = self.model.get_const('RPM0',True)
		self.R = self.model.get_const('R',True)
		self.L = self.model.get_const('L',True)
		self.J = self.model.get_const('J',True)

		self.r_prop = self.model.get_const('r_prop')
		self.r_d_1 = self.r_prop - self.d/2*zHat
		self.r_d_2 = self.r_prop + self.d/2*zHat

		self.b = self.Kt * I0 / (RPM0/60*2*pi)
		self.Ke = 60 / (2*pi*KV)

		Beta = thrust_torque_coeffs[:,0]
		CT = thrust_torque_coeffs[:,1]
		CQ = thrust_torque_coeffs[:,2]
		self.CT = lambda beta: interp(beta, Beta, CT)
		self.CQ = lambda beta: interp(beta, Beta, CQ)

		# default states
		self.I = 0
		self.omega = 0

		# default inputs
		self.epsilon = 0

	def calc_state_dot(self):
		self.I_dot = (self.epsilon - self.R*self.I - self.Ke*self.omega)/self.L
		self.omega_dot = (self.Kt*self.I - self.b*self.omega - self.Q)/self.J

	def calc_force_moments(self):
		U_p = self.model.U + cross(self.model.omega, self.model.ra_to_body(self.r_prop))
		U_p_ra_frame = self.model.Cra_b @ U_p
		u_p = U_p_ra_frame[0]
		self.w = self.w_f + (self.w_fs + self.w_f)*self.model.hull.area/self.model.hull.area0
		self.VA = u_p*(1-self.w)
		self.n = self.omega/(2*pi)
		self.Vrot = 0.7*pi*self.n*self.d
		Vr2 = self.VA**2 + self.Vrot**2
		if Vr2 < 1e-12:
			self.F_p, self.M_p = zero3, zero3
		else:
			self.beta = arctan2(self.VA, self.Vrot)
			z_d_2_world = self.model.ra_to_world(self.r_d_2)[2]
			z_d_1_world = self.model.ra_to_world(self.r_d_1)[2]
			self.fp = z_d_2_world / (z_d_2_world - z_d_1_world)
			self.fp = clip(self.fp, 0, 1)
			rho = self.model.rho_surf + (self.model.rho - self.model.rho_surf)*self.fp
			QA = 1/2*rho*Vr2*(pi/4*self.d**2)
			self.T = QA*self.CT(self.beta)
			self.Q = QA*self.CT(self.beta)*self.d
			self.F_p = self.model.Cb_ra @ array([self.eta_T*self.T, 0, 0])
			self.M_p = cross(self.model.ra_to_body(self.r_prop), self.F_p)