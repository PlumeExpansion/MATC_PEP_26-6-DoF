import numpy as np
from typing import TYPE_CHECKING
if TYPE_CHECKING:
	import model_RBird

from utils import *
from b_series_coeff import *

class Propulsor:
	def __init__(self, model: 'model_RBird.Model_6DoF'):
		self.model = model

		self.d = self.model.get_const('d',True)
		self.Z = self.model.get_const('Z',True)
		self.AE_AO = self.model.get_const('AE_AO',True)
		self.P_D = self.model.get_const('P_D',True)
		
		self.eta_T = self.model.get_const('eta_T',True)
		self.eta_Tr = self.model.get_const('eta_Tr',True)
		
		self.w_fs = self.model.get_const('w_fs',True)
		self.w_f = self.model.get_const('w_f',True)

		self.KV = self.model.get_const('KV',True)
		self.I0 = self.model.get_const('I0',True)
		self.R0 = self.model.get_const('R0',True)

		self.r_prop = self.model.get_const('r_prop')
		self.r_d_1 = self.r_prop - self.d/2*zHat
		self.r_d_2 = self.r_prop + self.d/2*zHat

		J = linspace(0, 1.6, 160)
		K_T, K_Q = b_series_coeff(self.AE_AO, self.P_D, J, self.Z)
		p_K_T = polyfit(J, K_T, 3)
		self.p_K_Q = polyfit(J, K_Q, 3)
		self.K_T = lambda J: polyval(p_K_T, J)
		self.K_Q = lambda J: polyval(self.p_K_Q, J)

		real_roots = [root.real for root in roots(p_K_T) if abs(root.imag) < 1e-6]
		if len(real_roots) == 0:
			self.model.init_errors += 1
			print(f'ERROR: advance coefficient limit not found')
		else:
			self.J_lim = max(real_roots)
		
		# default voltage
		self.epsilon = 0

	def calc_force_moment(self):
		U_p = self.model.U + cross(self.model.omega, self.model.ra_to_body(self.r_prop))
		U_p_ra_frame = self.model.Cra_b @ U_p
		u_p = U_p_ra_frame[0]
		self.w = self.w_f + (self.w_fs + self.w_f)*self.model.hull.area/self.model.hull.area0
		self.VA = u_p*(1-self.w)

		z_d_2_world = self.model.ra_to_world(self.r_d_2)[2]
		z_d_1_world = self.model.ra_to_world(self.r_d_1)[2]
		self.fp = z_d_2_world / (z_d_2_world - z_d_1_world)
		self.fp = clip(self.fp, 0, 1)
		rho = self.model.rho_surf + (self.model.rho - self.model.rho_surf)*self.fp

		self.__calc_n_J()

		if self.J > self.J_lim:
			n = self.VA/(self.J_lim*self.d)*sign(self.epsilon)
			K_Q = self.K_Q(self.J_lim)
			self.Q = K_Q*rho*n**2*self.d**5
			self.I = 2*pi/60*self.Q*self.KV + self.I0
			epsilon = 60*n/self.KV + self.I*self.R0
			print('WARNING: advance coefficient limit exceeded', end='')
			print(f', boosting voltage: {self.epsilon:.1f} -> {epsilon:.1f} V', end='')
			print(f', RPM: {int(60*self.n)} -> {int(60*n)}')
			self.epsilon = epsilon
			self.n = n
		else:
			K_Q = self.K_Q(self.J)
			self.Q = K_Q*self.model.rho*self.n**2*self.d**5
			self.I = 2*pi/60*self.Q*self.KV + self.I0

		self.P = self.epsilon*self.I
		self.eta_M = self.Q*2*pi*self.n/self.P
		K_T = self.K_T(self.J)
		self.eta0 = self.J*2*pi*(K_T/K_Q)
		self.eta = self.eta_M * self.eta0
		self.T = K_T*rho*self.n**2*self.d**4
		self.F_p = self.model.Cb_ra @ array([sign(n)*(self.eta_T if self.n > 0 else self.eta_Tr)*self.T, 0, 0])
		self.M_p = cross(self.model.ra_to_body(self.r_prop), self.F_p)
	
	def __calc_n_J(self):
		c1 = 2*pi*self.KV/60 * self.model.rho*self.VA*self.d**4
		c2 = self.R0/(abs(self.epsilon)-self.I0*self.R0) * self.VA/self.d
		c3 = 60/(self.R0*self.KV)

		coeffs = c1*c2*self.p_K_Q
		coeffs[1] -= 1
		coeffs[2] += c2*c3

		real_roots = [root.real for root in roots(coeffs) if abs(root.imag) < 1e-6]
		if len(real_roots) == 0:
			print(f'ERROR: advance coefficient root not found, falling back to nonresistive motor')
			self.n = self.epsilon*self.KV/60
			Vrot = 0.7*pi*self.n*self.d
			beta = arctan2(self.VA, Vrot)
			self.J = abs(0.7*pi*tan(beta))
		else:
			self.J = max(real_roots)
			self.n = sign(self.epsilon)*self.VA/(self.J*self.d)