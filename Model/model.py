import numpy as np
import numpy.linalg as la
import pandas as pd
from scipy.interpolate import LinearNDInterpolator
import sys

from utils import *
import panel

class Model_6DoF:
	def __init__(self, path_constants, path_hull, path_wing_root, prompt=False):
		self.constants = {}
		self.__load_params(path_constants, path_hull, path_wing_root, prompt)

		self.missing_constants = []
		self.accessed_constants = []
		self.__commit_params()
		
		self.Cb_ra = eye(3)
		self.Cra_b = eye(3)
		self.C0b = eye(3)
		self.Cb0 = eye(3)
		self.r_0 = eye(3)
		
		self.__make_panels()
		
		# handle missing constants
		if len(self.missing_constants) > 0:
			print(f'INFO: missing {len(self.missing_constants)} constants - {self.missing_constants}, exiting')
			sys.exit()
		
		# handle unaccessed constants
		unaccessed = list(set(self.constants) - set(self.accessed_constants))
		unaccessed.sort()
		if len(unaccessed) > 0:
			print(f'WARNING: {len(unaccessed)} unaccessed constants defined - {list(unaccessed)}', end='')
			if prompt:
				print(f', continue? (1-yes, 0-no): ')
				str = input()
				confirms = ['1', 'y', 'yes']
				if str not in confirms:
					sys.exit()

	def __load_params(self, path_constants, path_hull, path_wing_root, prompt):
		warnings = 0
		errors = 0
		# load model constants
		try:
			with open(path_constants,'r') as file:
				for line in file:
					# comment
					if line.startswith('#') or line.isspace():
						continue
					sep = line.find('=')
					key = line[:sep].strip()
					valueStr = line[sep+1:line.find('#')].strip()
					# blank
					if len(valueStr) == 0 or valueStr.isspace():
						print(f'WARNING: blank entry for key: {key}')
						warnings += 1
						continue
					# vector
					if valueStr.startswith('('):
						value = []
						for v in valueStr[1:-1].split(','):
							try:
								value.append(float(v))
							except:
								print(f'WARNING: nonfloat component for vector: {key} - {v}')
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
							print(f"WARNING: nonfloat value for key: {key} - {valueStr}")
							warnings += 1
							continue
					if key in self.constants:
						print(f"WARNING: repeated key: {key} - {valueStr} / {self.constants[key]}")
						warnings += 1
					self.constants[key] = value
					# print(f'DEBUG: key: {f"{key}":<12}\tvalue: {value}')
		except FileNotFoundError:
			print(f'ERROR: Model constants file not found - "{path_constants}"')
			errors += 1

		# load hull parameters
		input_cols = ['Z','Pitch','Roll']
		output_cols = ['Volume','Area','VCx','VCy','VCz','ACx','ACy','ACz']
		try:
			df = pd.read_csv(path_hull)
			df = df.apply(pd.to_numeric, errors='coerce')
			df_clean = df.dropna()
			missing_cols = set(input_cols + output_cols) - set(df.columns)
			if missing_cols:
				print(f'ERROR: Hull data missing columns {missing_cols}')
				errors += 1
			else:
				points = df_clean[input_cols].values
				values = df_clean[output_cols].values
				self.hull_interp = LinearNDInterpolator(points, values)
		except FileNotFoundError:
			print(f'ERROR: Hull data file not found - "{path_hull}"')
			errors += 1

		# load wing root parameters
		try:
			df = pd.read_csv(path_wing_root)
			df = df.apply(pd.to_numeric, errors='coerce')
			df_clean = df.dropna()
			missing_cols = set(input_cols + output_cols) - set(df.columns)
			if missing_cols:
				print(f'ERROR: Wing root data missing columns {missing_cols}')
				errors += 1
			else:
				points = df_clean[input_cols].values
				values = df_clean[output_cols].values
				self.wing_root_interp = LinearNDInterpolator(points, values)
		except FileNotFoundError:
			print(f'ERROR: Wing root data file not found - "{path_wing_root}"')
			errors += 1

		# handle errors
		if errors > 0:
			print(f'INFO: {errors} errors detected, exiting')
			sys.exit()
		
		# handle warnings
		if warnings > 0:
			print(f'INFO: Loaded parameters with {warnings} warnings', end='')
			if prompt:
				print(f', continue? (1-yes, 0-no): ')
				str = input()
				confirms = ['1', 'y', 'yes']
				if str not in confirms:
					sys.exit()

	def __commit_params(self):
		self.m = self.__get_const('m')
		self.g = self.__get_const('g')
		self.rho = self.__get_const('rho')

		Ixx = self.__get_const('Ixx')
		Iyy = self.__get_const('Iyy')
		Izz = self.__get_const('Izz')
		Ixy = self.__get_const('Ixy')
		Ixz = self.__get_const('Ixz')
		Iyz = self.__get_const('Iyz')

		if None not in [Ixx, Iyy, Izz, Ixy, Ixz, Iyz]:
			self.Ib = array([
				[Ixx, Ixy, Ixz],
				[Ixy, Iyy, Iyz],
				[Ixz, Iyz, Izz]
			])
		
		self.r_CM = self.__get_const('r_CM')
		self.r_ra = self.__get_const('r_ra')
		self.r_prop = self.__get_const('r_prop')

	def __get_const(self, key):
		if key in self.constants:
			self.accessed_constants.append(key)
			return self.constants[key]
		else:
			if key not in self.missing_constants:
				self.missing_constants.append(key)
				print(f'ERROR: missing constant: {key}')

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
		r_LE_1 = self.__get_const('r_LE_'+id_1)
		r_LE_2 = self.__get_const('r_LE_'+id_2)
		r_TE_1 = self.__get_const('r_TE_'+id_1)
		r_TE_2 = self.__get_const('r_TE_'+id_2)
		C_L0 = self.__get_const('C_L'+id+'_0')
		C_Lalpha = self.__get_const('C_L'+id+'_alpha')
		C_D0 = self.__get_const('C_D'+id+'_0')
		eff = self.__get_const('e_'+id)
		if all([r is not None for r in [r_LE_1,r_LE_2,r_TE_1,r_TE_2]]) and None not in [C_L0,C_Lalpha,C_D0,eff]:
			panel_left = panel.Panel(self, r_LE_1, r_LE_2, r_TE_1, r_TE_2,
							C_L0, C_Lalpha, C_D0, eff, rear)
			panel_right = panel.Panel(self, flipY@r_LE_1, flipY@r_LE_2, flipY@r_TE_1, flipY@r_TE_2,
							C_L0, C_Lalpha, C_D0, eff, rear)
			return panel_left, panel_right
		else:
			return None, None

	def __make_hull(self):
		pass

	def __make_wing_roots(self):
		pass

	def __make_propulsion(self):
		pass

	def ra_to_body(self, r):
		return self.r_ra + self.Cb_ra @ r
	def ra_to_world(self, r):
		return self.C0b @ self.ra_to_body(r) + self.r_0
	def body_to_world(self, r):
		return self.C0b @ r + self.r_0
			
if __name__ == '__main__':
	Model_6DoF('model_constants.txt','hull_data.csv','left_wing_root_data.csv')