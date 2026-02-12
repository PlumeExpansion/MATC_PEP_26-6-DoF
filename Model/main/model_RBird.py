import numpy as np

from utils import *
import panel, hull, wing_root, propulsor

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
		self.U = zeros(3)
		self.omega = zeros(3)
		self.Phi = zeros(3)
		self.r = zeros(3)

		# default inputs
		self.psi_ra = 0
		
		make_errors = 0
		print('INFO: making panels...')
		make_errors += self.__make_panels(path_aero_coeffs_root)
		print('INFO: making hull...')
		make_errors += self.__make_hull(path_hull, path_aero_coeffs_root)

		print('INFO: making wing roots')
		make_errors += self.__make_wing_roots(path_wing_root, path_aero_coeffs_root)
		print('INFO: making propulsor')
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
			print(f'\nINFO: {self.init_errors} initialization error(s)', end='')
		else:
			print(f'INFO: model intialized succesfully')
		
		if to_exit:
			print(f', exiting')
			exit()

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

		self.Ib = array([
			[Ixx, Ixy, Ixz],
			[Ixy, Iyy, Iyz],
			[Ixz, Iyz, Izz]
		])

		self.Ib_inv = LA.inv(self.Ib)
		
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

		self.panels: dict[str, tuple[panel.Panel, panel.Panel]] = {}
		errors = 0

		for id, params in panel_params.items():
			L, R, err = self.__make_panel(id, params[0], params[1], root)
			if L and R:
				self.panels[id] = (L, R)
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

		panel_left = panel.Panel(self, id, r_list, aero_coeffs, rear)
		panel_right = panel.Panel(self, id, [flipY @ r for r in r_list], aero_coeffs, rear)
		return panel_left, panel_right, 0

	def __make_hull(self, path_hull, path_aero_coeffs_root):
		try:
			g_linear, f_linear, f_nearest = interp_volume_area(load_volume_area_data(path_hull))
		except Exception as e:
			print(f'ERROR: failed to load hull volume area data - {e}')
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
			self.hull = hull.Hull(self, g_linear, f_linear, f_nearest, hull_aero_coeffs, surf_aero_coeffs)
		except Exception as e:
			print(f'ERROR: failed to make hull - {e}')
			return 1
		return 0

	def __make_wing_roots(self, path_wing_root, path_aero_coeffs_root):
		try:
			df = load_volume_area_data(path_wing_root)
			g_linear_L, f_linear_L, f_nearest_L = interp_volume_area(df)
			df[['Roll','VCy','ACy']] *= -1
			g_linear_R, f_linear_R, f_nearest_R = interp_volume_area(df)
		except Exception as e:
			print(f'ERROR: failed to load wing root volume area data - {e}')
			return 1
		try:
			aero_coeffs = load_aero_coeffs(path_aero_coeffs_root+'wing_root.txt')
		except Exception as e:
			print(f'ERROR: failed to load wing root aerodynamic coefficients - {e}')
			return 1
		wr_L = wing_root.WingRoot(self, g_linear_L, f_linear_L, f_nearest_L, aero_coeffs, True)
		wr_R = wing_root.WingRoot(self, g_linear_R, f_linear_R, f_nearest_R, aero_coeffs, False)
		self.wing_roots = (wr_L, wr_R)
		return 0

	def __make_propulsor(self, path_propulsion):
		try:
			thrust_torque_coeffs = load_propulsor_data(path_propulsion)
		except Exception as e:
			print(f'ERROR: failed to load propulsor data - {e}')
			return 1
		self.propulsor = propulsor.Propulsor(self, thrust_torque_coeffs)
		return 0

	def __calc_query(self):
		z = self.body_to_world(-self.r_CM)[2]
		pitch = self.omega[1]
		roll = self.omega[0]
		self.query = array([z, pitch, roll])

	def calc_state_dot(self):
		F = zero3.copy()
		M = zero3.copy()
		self.__calc_rot_mats()
		self.__calc_query()

		for panels in self.panels.values():
			for panel in panels:
				panel.calc_force_moments()
				F += panel.F_f
				M += panel.M_f

		for wr in self.wing_roots:
			wr.calc_force_moments()
			F += wr.F_f + wr.F_b
			M += wr.M_f + wr.M_b
		
		self.hull.calc_force_moments()
		F += self.hull.F_h + self.hull.F_b + self.hull.F_surf
		M += self.hull.M_h + self.hull.M_b + self.hull.M_surf

		self.propulsor.calc_force_moments()
		F += self.propulsor.F_p
		M += self.propulsor.M_p

		F_g = self.Cb0 @ array([0, 0, self.m*self.g])
		F += F_g

		self.U_dot = F/self.m - cross(self.omega, self.U)
		self.omega_dot = self.Ib_inv @ (M - cross(self.omega, self.Ib @ self.omega))
		self.__calc_H()
		self.Phi_dot = self.H @ self.Phi
		self.r_dot = self.C0b @ self.U

	def __calc_H(self):
		phi = self.Phi[0]
		theta = self.Phi[1]
		self.H = array([
			[1, sin(phi)*tan(theta), cos(phi)*tan(theta)],
			[0, cos(phi), -sin(phi)],
			[0, sin(phi)/cos(theta), cos(phi)/cos(theta)]
		])

	def __calc_rot_mats(self):
		phi = self.Phi[0]
		theta = self.Phi[1]
		psi = self.Phi[2]
		C10 = array([
			[cos(psi), sin(psi), 0],
			[-sin(psi), cos(psi), 0],
			[0, 0, 1]
		]) 
		C21 = array([
			[cos(theta), 0, -sin(theta)],
			[0, 1, 0],
			[sin(theta), 0, cos(theta)]
		])
		Cb2 = array([
			[1, 0, 0],
			[0, cos(phi), sin(phi)],
			[0, -sin(phi), cos(phi)]
		])
		self.Cb0 = Cb2 @ C21 @ C10
		self.C0b = transpose(self.Cb0)
		self.Cb_ra = np.array([
			[cos(self.psi_ra), -sin(self.psi_ra), 0],
			[sin(self.psi_ra), cos(self.psi_ra), 0],
			[0, 0, 1]
		])
		self.Cra_b = transpose(self.Cb_ra)

	def get_state(self):
		return concatenate((self.U, self.omega, self.Phi, self.r))
	def get_state_dot(self):
		return concatenate((self.U_dot, self.omega_dot, self.Phi_dot, self.r_dot))
	def set_state(self, state):
		self.U = state[0:3]
		self.omega = state[3:6]
		self.Phi = state[6:9]
		self.r = state[9:12]
	
	def get_input(self):
		return self.psi_ra
	def set_input(self, input):
		self.psi_ra = input

	def ra_to_body(self, r):
		return self.r_ra + self.Cb_ra @ r
	def ra_to_world(self, r):
		return self.C0b @ self.ra_to_body(r) + self.r
	def body_to_world(self, r):
		return self.C0b @ r + self.r

def make_default():
	return Model_6DoF('params/model_constants.txt','params/hull_data.csv','params/left_wing_root_data.csv',
			'params/sample aero coeffs/','params/4 quad prop data/thrust torque coeffs/B4-70-14.txt')

def main():
	make_default()

if __name__ == '__main__': main()
