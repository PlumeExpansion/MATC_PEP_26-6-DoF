import numpy as np
import numpy.linalg as la
import pandas as pd
from scipy.interpolate import LinearNDInterpolator, NearestNDInterpolator
import sys

from utils import *
import panel, hull, wing_root, propulsor

class Model_6DoF:
	def __init__(self, path_constants, path_hull, path_wing_root, prompt=False):
		self.constants = {}
		(hull_grounded_interp_nd, hull_floating_interp_nd, hull_floating_interp_near, 
   			wing_root_grounded_interp_nd, wing_root_floating_interp_nd, wing_root_floating_interp_near
		) = self.__load_params(path_constants, path_hull, path_wing_root, prompt)

		self.missing_constants = set()
		self.accessed_constants = set()
		self.invalid_constants = set()
		self.init_errors = 0
		self.__commit_params()
		
		# initalize default rotation matrices
		self.Cb_ra = eye(3)
		self.Cra_b = eye(3)
		self.C0b = eye(3)
		self.Cb0 = eye(3)

		# initialize default states
		self.U = zeros(3)
		self.omega = zeros(3)
		self.Phi = zeros(3)
		self.r_0 = zeros(3)
		
		self.__make_panels()
		self.__make_hull(hull_grounded_interp_nd, hull_floating_interp_nd, hull_floating_interp_near)
		self.__make_wing_roots(wing_root_grounded_interp_nd, wing_root_floating_interp_nd, wing_root_floating_interp_near)
		self.__make_propulsion()

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
			print(f'WARNING: {len(unaccessed)} unaccessed constant(s) defined - {list(unaccessed)}', end='')
			if prompt and not to_exit:
				print(f', continue? (1-yes, 0-no): ')
				str = input()
				confirms = ['1', 'y', 'yes']
				if str not in confirms:
					sys.exit()
			else:
				print()
		
		if len(to_fix) > 0:
			print(f'INFO: {len(to_fix)} constant(s) to fix - {to_fix}', end='')

		if self.init_errors > 0:
			print(f'\nINFO: {self.init_errors} initialization error(s)', end='')
		
		if to_exit:
			print(f', exiting')
			sys.exit()

	def __load_params(self, path_constants, path_hull, path_wing_root, prompt):
		warnings = 0
		errors = 0
		# load model constants
		try:
			with open(path_constants,'r') as file:
				for line_num, line in enumerate(file, 1):
					# comment
					if line.startswith('#') or line.isspace():
						continue
					line = line.strip()
					content = line.split('#')[0].strip()
					sep = content.find('=')
					# no assignment
					if sep == -1:
						print(f'WARNING: line ({line_num}) - invalid row: {line}')
						warnings += 1
						continue
					key = content[:sep].strip()
					# no key
					if len(key) == 0 or key.isspace():
						print(f'WARNING: line ({line_num}) - blank key for row: {line}')
						warnings += 1
						continue
					valueStr = content[sep+1:].strip()
					# blank
					if len(valueStr) == 0 or valueStr.isspace():
						print(f'WARNING: line ({line_num}) - blank value for key: {key}')
						warnings += 1
						continue
					# vector
					if valueStr.startswith('('):
						value = []
						for v in valueStr[1:-1].split(','):
							try:
								value.append(float(v))
							except:
								print(f'WARNING: line ({line_num}) - nonfloat component for vector: {key} = {v}')
								warnings += 1
								continue
						if len(value) != 3:
							continue
						value = array(value)
						if not key.startswith('r_'): key = 'r_' + key
					# scalar
					else:
						try:
							value = float(valueStr)
						except:
							print(f"WARNING: line ({line_num}) - nonfloat value for entry: {key} = {valueStr}")
							warnings += 1
							continue
					if key in self.constants:
						print(f"WARNING: line ({line_num}) - repeated entry: {key} = {valueStr} = {self.constants[key]}")
						warnings += 1
					self.constants[key] = value
					# print(f'DEBUG: line ({line_num}) - key: {f"{key}":<12}\tvalue: {f"{value}":<12}\tvalueStr: {valueStr}')
		except FileNotFoundError:
			print(f'ERROR: Model constants file not found - "{path_constants}"')
			errors += 1

		# load hull parameters
		input_cols = ['Z','Pitch','Roll']
		grounded_cols = ['Volume','Area']
		floating_cols = ['VCx','VCy','VCz','ACx','ACy','ACz']
		try:
			df = pd.read_csv(path_hull)
			df = df.apply(pd.to_numeric, errors='coerce')
			missing_cols = set(input_cols + grounded_cols + floating_cols) - set(df.columns)
			if missing_cols:
				print(f'ERROR: Hull data missing column(s) {missing_cols}')
				errors += 1
			else:
				df_grounded = df.dropna(subset=grounded_cols)
				df_floating = df.dropna(subset=floating_cols)
				inputs_grounded = df_grounded[input_cols].values
				inputs_floating = df_floating[input_cols].values
				outputs_grounded = df_grounded[grounded_cols].values
				outputs_floating = df_floating[floating_cols].values
				hull_grounded_interp_nd = LinearNDInterpolator(inputs_grounded, outputs_grounded)
				hull_floating_interp_nd = LinearNDInterpolator(inputs_floating, outputs_floating)
				hull_floating_interp_near = NearestNDInterpolator(inputs_floating, outputs_floating)
		except FileNotFoundError:
			print(f'ERROR: Hull data file not found - "{path_hull}"')
			errors += 1

		# load wing root parameters
		try:
			df = pd.read_csv(path_wing_root)
			df = df.apply(pd.to_numeric, errors='coerce')
			missing_cols = set(input_cols + grounded_cols + floating_cols) - set(df.columns)
			if missing_cols:
				print(f'ERROR: Wing root data missing column(s) {missing_cols}')
				errors += 1
			else:
				df_grounded = df.dropna(subset=grounded_cols)
				df_floating = df.dropna(subset=floating_cols)
				inputs_grounded = df_grounded[input_cols].values
				inputs_floating = df_floating[input_cols].values
				outputs_grounded = df_grounded[grounded_cols].values
				outputs_floating = df_floating[floating_cols].values
				wing_root_grounded_interp_nd = LinearNDInterpolator(inputs_grounded, outputs_grounded)
				wing_root_floating_interp_nd = LinearNDInterpolator(inputs_floating, outputs_floating)
				wing_root_floating_interp_near = NearestNDInterpolator(inputs_floating, outputs_floating)
		except FileNotFoundError:
			print(f'ERROR: Wing root data file not found - "{path_wing_root}"')
			errors += 1
		
		# handle warnings
		if warnings > 0:
			print(f'INFO: Loaded parameters with {warnings} warning(s)', end='')
			if prompt and not errors > 0:
				print(f', continue? (1-yes, 0-no): ')
				str = input()
				confirms = ['1', 'y', 'yes']
				if str not in confirms:
					sys.exit()
			else:
				print()
		
		# handle errors
		if errors > 0:
			print(f'INFO: {errors} error(s) detected, exiting')
			sys.exit()

		return (hull_grounded_interp_nd, hull_floating_interp_nd, hull_floating_interp_near, 
				wing_root_grounded_interp_nd, wing_root_floating_interp_nd, wing_root_floating_interp_near)

	def __commit_params(self):
		self.m = self.get_const('m',True)
		self.g = self.get_const('g',True)
		self.rho = self.get_const('rho',True)
		self.rho_surf = self.get_const('rho_surf',True)

		Ixx = self.get_const('Ixx',True)
		Iyy = self.get_const('Iyy',True)
		Izz = self.get_const('Izz',True)
		Ixy = self.get_const('Ixy',True)
		Ixz = self.get_const('Ixz',True)
		Iyz = self.get_const('Iyz',True)

		self.Ib = array([
			[Ixx, Ixy, Ixz],
			[Ixy, Iyy, Iyz],
			[Ixz, Iyz, Izz]
		])
		
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

	def __make_panels(self):
		self.panel_v_L, self.panel_v_R = self.__make_panel('vr','v1','v')
		self.panel_1_L, self.panel_1_R = self.__make_panel('v1','12','1')
		self.panel_2_L, self.panel_2_R = self.__make_panel('12','23','2')
		self.panel_3_L, self.panel_3_R = self.__make_panel('23','3t','3')

		self.panel_r1_L, self.panel_r1_R = self.__make_panel('r1t','r12','r1')
		self.panel_r2_L, self.panel_r2_R = self.__make_panel('r12','r2m','r2')
		self.panel_rv_L, self.panel_rv_R = self.__make_panel('rvs','r12v','rv')
		self.panel_rs_L, self.panel_rs_R = self.__make_panel('rsr','rvs','rs')

	def __make_panel(self, id_1, id_2, id):
		rear = id.startswith('r')
		r_LE_1 = self.get_const('r_LE_'+id_1)
		r_LE_2 = self.get_const('r_LE_'+id_2)
		r_TE_1 = self.get_const('r_TE_'+id_1)
		r_TE_2 = self.get_const('r_TE_'+id_2)
		C_L0 = self.get_const('C_L'+id+'_0')
		C_Lalpha = self.get_const('C_L'+id+'_alpha',True)
		C_D0 = self.get_const('C_D'+id+'_0',True)
		eff = self.get_const('e_'+id,True)
		r_list = [r_LE_1,r_LE_2,r_TE_1,r_TE_2]

		panel_left = panel.Panel(self, id, [r - self.r_CM for r in r_list],
						C_L0, C_Lalpha, C_D0, eff, rear)
		panel_right = panel.Panel(self, id, [flipY @ (r - self.r_CM) for r in r_list],
						C_L0, C_Lalpha, C_D0, eff, rear)
		return panel_left, panel_right

	def __make_hull(self, hull_grounded_interp_nd, hull_floating_interp_nd, hull_floating_interp_near):
		self.hull = hull.Hull(self, hull_grounded_interp_nd, hull_floating_interp_nd, hull_floating_interp_near)

	def __make_wing_roots(self, wing_root_grounded_interp_nd, wing_root_floating_interp_nd, wing_root_floating_interp_near):
		self.wing_root_L = wing_root.WingRoot(self, wing_root_grounded_interp_nd, wing_root_floating_interp_nd, 
										wing_root_floating_interp_near, True)
		self.wing_root_R = wing_root.WingRoot(self, wing_root_grounded_interp_nd, wing_root_floating_interp_nd, 
										wing_root_floating_interp_near, False)

	def __make_propulsion(self):
		self.propulsor = propulsor.Propulsor(self)

	def __calc_query(self):
		z = self.body_to_world(-self.r_CM)
		pitch = self.omega[1]
		roll = self.omega[0]
		self.query = array([z, pitch, roll])

	def calc_state_dot(self):
		pass

	def ra_to_body(self, r):
		return self.r_ra + self.Cb_ra @ r
	def ra_to_world(self, r):
		return self.C0b @ self.ra_to_body(r) + self.r_0
	def body_to_world(self, r):
		return self.C0b @ r + self.r_0
			
if __name__ == '__main__':
	Model_6DoF('model_constants.txt','hull_data.csv','left_wing_root_data.csv')