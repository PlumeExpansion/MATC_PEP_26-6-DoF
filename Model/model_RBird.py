import numpy as np

from utils.utils import *
from components.panel import Panel
from components.hull import Hull
from components.propulsor import Propulsor
from components.wing_root import WingRoot

class Model_6DoF:
	def __init__(self, path_constants, path_hull, path_wing_root, path_aero_coeffs_root, path_propulsor):
		self.missing_constants = set()
		self.accessed_constants = set()
		self.invalid_constants = set()
		self.init_errors = 0
		print('INFO: loading constants')
		try:
			self.constants = load_constants(path_constants)
			self.__commit_params()
		except Exception as e:
			print(f'ERROR: failed to load constants - {e}')
			self.init_errors += 1

		# default states
		self.U = np.zeros(3)
		self.omega = np.zeros(3)
		self.Phi = np.zeros(3)
		self.r = np.zeros(3)

		# default inputs
		self.psi_ra = 0

		make_errors = 0
		print('INFO: making panels...')
		make_errors += self.__make_panels(path_aero_coeffs_root)
		print('INFO: making hull...')
		make_errors += self.__make_hull(path_hull, path_aero_coeffs_root)

		print('INFO: making wing roots...')
		make_errors += self.__make_wing_roots(path_wing_root, path_aero_coeffs_root)
		print('INFO: making propulsor...')
		make_errors += self.__make_propulsor(path_propulsor)
		print(f'INFO: components initialized with {make_errors} error(s)')
		self.init_errors += make_errors

		to_fix = list(self.missing_constants.union(self.invalid_constants))
		to_fix.sort()
		to_exit = len(to_fix) > 0 or self.init_errors > 0

		# handle missing constants
		missing = list(self.missing_constants)
		missing.sort()
		if len(missing) > 0:
			print(f'INFO: missing {len(missing)} constant(s) - {missing}')
		
		# handle invalid constants
		invalid = list(self.invalid_constants)
		invalid.sort()
		if len(invalid) > 0:
			print(f'INFO: {len(invalid)} invalid constant(s) - {invalid}')
		
		# handle unaccessed constants
		unaccessed = list(set(self.constants) - set(self.accessed_constants))
		unaccessed.sort()
		if len(unaccessed) > 0:
			print(f'WARNING: {len(unaccessed)} unaccessed constant(s) defined - {list(unaccessed)}')
		
		if len(to_fix) > 0:
			print(f'INFO: {len(to_fix)} constant(s) to fix - {to_fix}', end='')

		if self.init_errors > 0:
			print(f'INFO: {self.init_errors} initialization error(s)', end='')
		else:
			print(f'INFO: model intialized succesfully')
		
		if to_exit:
			print(f', exiting')
			exit()

		self.calc_state_dot()

	def __commit_params(self):
		self.m = self.get_const('m',True)
		self.g = self.get_const('g',True)
		self.rho = self.get_const('rho',True)
		self.rho_surf = self.get_const('rho_surf',True)

		Ixx = self.get_const('Ixx',True)
		Iyy = self.get_const('Iyy',True)
		Izz = self.get_const('Izz',True)
		Ixy = self.get_const('Ixy')
		Ixz = self.get_const('Ixz')
		Iyz = self.get_const('Iyz')

		self.Ib = np.array([
			[Ixx, Ixy, Ixz],
			[Ixy, Iyy, Iyz],
			[Ixz, Iyz, Izz]
		]).astype(np.float64)

		self.Ib_inv = LA.inv(self.Ib).astype(np.float64)
		
		self.r_CM = self.get_const('r_CM')
		self.r_ra = self.get_const('r_ra')

	def get_const(self, key, pos_check=False):
		if key in self.constants:
			self.accessed_constants.add(key)
			value = self.constants[key]
			if pos_check and value <= 0:
				self.invalid_constants.add(key)
				print(f'ERROR: nonpositive value for entry: {key} = {value}')
				return 1.0
			return value
		else:
			if key not in self.missing_constants:
				self.missing_constants.add(key)
				print(f'ERROR: missing constant: {key}')
		return one3 if key.startswith('r_') else 1

	def __make_panels(self, root):
		panel_params = {
			'v': ('vr', 'v1'),
			'1': ('v1', '12'),
			'2': ('12', '23'),
			'3': ('23', '3t'),
			'r1': ('r1t', 'r12'),
			'r2': ('r12', 'r2m'),
			'rv': ('rvs', 'r12v'),
			'rs': ('rsr', 'rvs'),
		}

		self.panels: dict[str, Panel] = {}
		errors = 0

		for id, params in panel_params.items():
			L, R, err = self.__make_panel(id, params[0], params[1], root)
			if L and R:
				self.panels[L.id] = L
				self.panels[R.id] = R
			else:
				errors += err

		return err

	def __make_panel(self, id, id_1, id_2, root):
		try:
			aero_coeffs = load_aero_coeffs(root+f'wing_{id}.txt')
		except Exception as e:
			print(f'ERROR: failed to load panel {id} aerodynamic coefficients - {e}')
			return None, None, 1
		
		rear = id.startswith('r')
		r_LE_1 = self.get_const('r_LE_'+id_1)
		r_LE_2 = self.get_const('r_LE_'+id_2)
		r_TE_1 = self.get_const('r_TE_'+id_1)
		r_TE_2 = self.get_const('r_TE_'+id_2)
		r_list = [r - self.r_CM for r in [r_LE_1,r_LE_2,r_TE_1,r_TE_2]]

		panel_left = Panel(self, id+'L', r_list, aero_coeffs, rear)
		panel_right = Panel(self, id+'R', [flipY @ r for r in r_list], aero_coeffs, rear)
		return panel_left, panel_right, 0

	def __make_hull(self, path_hull, path_aero_coeffs_root):
		try:
			vol_area_data = load_volume_area_data(path_hull)
		except Exception as e:
			print(f'ERROR: failed to load/interpolate hull volume area data - {e}')
			return 1
		try:
			hull_aero_coeffs = load_aero_coeffs(path_aero_coeffs_root+'hull.txt')
		except Exception as e:
			print(f'ERROR: failed to load hull aerodynamic coefficients - {e}')
			return 1
		try:
			surf_aero_coeffs = load_aero_coeffs(path_aero_coeffs_root+'surf.txt')
		except Exception as e:
			print(f'ERROR: failed to load surfaced aerodynamic coefficients - {e}')
			return 1
		try:
			self.hull = Hull(self, vol_area_data, hull_aero_coeffs, surf_aero_coeffs)
		except Exception as e:
			print(f'ERROR: failed to make hull - {e}')
			return 1
		return 0

	def __make_wing_roots(self, path_wing_root, path_aero_coeffs_root):
		try:
			vol_area_data = load_volume_area_data(path_wing_root)
		except Exception as e:
			print(f'ERROR: failed to load/interpolate wing root volume area data - {e}')
			return 1
		try:
			aero_coeffs = load_aero_coeffs(path_aero_coeffs_root+'wing_root.txt')
		except Exception as e:
			print(f'ERROR: failed to load wing root aerodynamic coefficients - {e}')
			return 1
		wr_L = WingRoot(self, vol_area_data, aero_coeffs, True)
		wr_R = WingRoot(self, vol_area_data, aero_coeffs, False)
		self.wing_roots = (wr_L, wr_R)
		return 0

	def __make_propulsor(self, path_propulsion):
		try:
			thrust_torque_coeffs = load_thrust_torque_coeffs(path_propulsion)
		except Exception as e:
			print(f'ERROR: failed to load propulsor data - {e}')
			return 1
		self.propulsor = Propulsor(self, thrust_torque_coeffs)
		return 0

	def calc_state_dot(self):
		(self.Cb0, self.C0b, self.Cb_ra, self.Cra_b, self.C0_ra, 
   			self.r_ra_world) = calc_base_rot_mats(self.Phi, self.psi_ra, self.r_ra)
		self.query = calc_base_query(self.C0b, self.r_CM, self.r, self.Phi)

		F, M = zero3.copy(), zero3.copy()

		for panel in self.panels.values():
			panel.calc_force_moments()
			F += panel.F
			M += panel.M

		for wr in self.wing_roots:
			wr.calc_force_moments()
			F += wr.F_b + wr.F_f
			M += wr.M_b + wr.M_f
		
		self.hull.calc_force_moments()
		F += self.hull.F_h + self.hull.F_b + self.hull.F_surf
		M += self.hull.M_h + self.hull.M_b + self.hull.M_surf

		self.propulsor.calc_force_moments()
		self.propulsor.calc_state_dot()
		F += self.propulsor.F
		M += self.propulsor.M

		(self.U_dot, self.omega_dot, self.Phi_dot, self.r_dot, 
   			self.H) = calc_state_dot(F,M, self.Cb0, self.C0b, self.m, self.g, self.Ib, self.Ib_inv, self.U, self.omega, self.Phi)

	def get_state(self):
		return np.concatenate((self.U, self.omega, self.Phi, self.r, self.propulsor.get_state()))
	def get_state_dot(self):
		return np.concatenate((self.U_dot, self.omega_dot, self.Phi_dot, self.r_dot, self.propulsor.get_state_dot()))
	def set_state(self, state):
		self.U = state[0:3]
		self.omega = state[3:6]
		self.Phi = state[6:9]
		self.r = state[9:12]
		self.propulsor.set_state(state[12:14])
	
	def get_input(self):
		return np.array([self.psi_ra, self.propulsor.get_input()])
	def set_input(self, input):
		self.psi_ra = input[0]
		self.propulsor.set_input(input[1])

@njit(cache=True)
def calc_state_dot(F,M, Cb0,C0b, m,g, Ib,Ib_inv, U,omega,Phi):
	F = F.astype(np.float64)
	M = M.astype(np.float64)
	U = U.astype(np.float64)
	omega = omega.astype(np.float64)

	F_g = Cb0 @ np.array([0.0, 0.0, m*g])
	F += F_g

	U_dot = F/m - cross(omega, U)
	omega_dot = Ib_inv @ (M - cross(omega, Ib @ omega))
	H = calc_H(Phi)
	Phi_dot = H @ Phi.astype(np.float64)
	r_dot = C0b @ U
	return U_dot, omega_dot, Phi_dot, r_dot, H

def make_default():
	return Model_6DoF('params/model_constants.txt','params/hull_data_regular_grid.npz','params/left_wing_root_data_regular_grid.npz',
			'params/sample aero coeffs/','params/4 quad prop data/thrust torque coeffs/B4-70-14.txt')

def main():
	import cProfile
	import pstats

	model = make_default()
	# with cProfile.Profile() as make_profile:
	# 	model = make_default()
	with cProfile.Profile() as state_dot_profile:
		model.calc_state_dot()
	print(model.hull.z0)
	# results = pstats.Stats(make_profile)
	# results.sort_stats(pstats.SortKey.TIME)
	# results.print_stats()
	# results.dump_stats('make_model.prof')
	results = pstats.Stats(state_dot_profile)
	results.dump_stats('calc_state_dot.prof')

if __name__ == '__main__': main()
