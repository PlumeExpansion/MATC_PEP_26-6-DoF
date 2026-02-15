import numpy as np

from typing import TYPE_CHECKING
if TYPE_CHECKING:
	from model_RBird import Model_6DoF
from utils.utils import *

class Propulsor:
	def __init__(self, model: 'Model_6DoF', thrust_torque_coeffs):
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

		self.thrust_torque_coeffs = thrust_torque_coeffs

		# default states
		self.I = 0
		self.omega = 0

		# default inputs
		self.epsilon = 0

	def get_state(self):
		return np.array([self.I, self.omega])
	def get_state_dot(self):
		return np.array([self.I_dot, self.omega_dot])
	def set_state(self, state):
		self.I = state[0]
		self.omega = state[1]

	def get_input(self):
		return self.epsilon
	def set_input(self, input):
		self.epsilon = input

	def calc_state_dot(self):
		self.I_dot = (self.epsilon - self.R*self.I - self.Ke*self.omega)/self.L
		self.omega_dot = (self.Kt*self.I - self.b*self.omega - self.Q)/self.J

	def calc_force_moments(self):
		u_p = calc_U_p(self.model.U, self.model.omega, ra_to_body(self.r_prop, self.model.Cb_ra, self.model.r_ra), self.model.Cra_b)
		self.w = self.w_f + (self.w_fs + self.w_f)*self.model.hull.area/self.model.hull.area0
		self.VA = u_p*(1-self.w)
		self.n = self.omega/(2*pi)
		self.Vrot = 0.7*pi*self.n*self.d
		z_d_2_world = ra_to_world(self.r_d_2, self.model.C0_ra, self.model.r_ra_world)[2]
		z_d_1_world = ra_to_world(self.r_d_1, self.model.C0_ra, self.model.r_ra_world)[2]
		(self.beta, self.fp, self.T, 
   			self.Q, self.F, self.M) = calc_thrust_torque(self.VA, self.Vrot, z_d_2_world, z_d_1_world,
												  self.model.rho_surf, self.model.rho, self.d, self.thrust_torque_coeffs, self.eta_T,
												  self.model.Cb_ra, self.r_prop)

@njit(cache=True)
def calc_U_p(U, omega, r_prop_body, Cra_b):
	U_p = U + cross(omega, r_prop_body)
	U_p_ra_frame = Cra_b @ U_p
	return U_p_ra_frame[0]

@njit(cache=True)
def calc_thrust_torque(VA,Vrot, z_d_2_world, z_d_1_world, rho_surf,rho, d, thrust_torque_coeffs,eta_T, Cb_ra, r_prop_body):
	beta = atan2(VA, Vrot)
	fp = z_d_2_world / (z_d_2_world - z_d_1_world)
	fp = clip(fp, 0, 1)
	Vr2 = VA**2 + Vrot**2
	if Vr2 < 1e-12:
		return 0, fp, 0, 0, np.zeros(3), np.zeros(3)
	rho = rho_surf + (rho - rho_surf)*fp
	QA = 1/2*rho*Vr2*(pi/4*d**2)
	T, Q = QA * query_periodic_1D(thrust_torque_coeffs, beta)
	F = Cb_ra @ np.array([eta_T*T, 0, 0])
	M = cross(r_prop_body, F)
	return beta, fp, T, Q, F, M