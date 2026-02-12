import numpy as np
import pandas as pd
import numpy.linalg as LA
from scipy.interpolate import LinearNDInterpolator, NearestNDInterpolator
from numpy import (cos, sin, tan, pi, transpose, 
				   arccos, arcsin, arctan2, 
				   cross, array, min, max, clip, sign, sqrt, 
				   eye, zeros, ones, concatenate, 
				   polyfit, polyval, roots, linspace, interp,
				   rad2deg, deg2rad)

xHat = array([1, 0 ,0])
yHat = array([0, 1 ,0])
zHat = array([0, 0 ,1])

zero3 = zeros(3)
one3 = ones(3)
eye3 = eye(3)

projYZ = array([
	[0, 0, 0],
	[0, 1 ,0],
	[0, 0, 1]
])

flipY = array([
	[1, 0, 0],
	[0, 1, 0],
	[0, 0, 1]
])

def unit(vec):
	return vec / mag(vec)

def mag(vec):
	return LA.norm(vec)

def stab_frame(U, omega, X, C_loc_ref):
	U_local = U + cross(omega, X)
	U_local_loc_frame = C_loc_ref @ U_local
	U_mag = mag(U_local)
	if U_mag < 1e-6:
		return U_mag, 0, 0, eye3
	alpha = arctan2(U_local_loc_frame[2], U_local[0])
	beta = arcsin(U_local_loc_frame[1] / U_mag)
	C_loc_stab = array([
		[cos(alpha)*sin(beta), -cos(alpha)*sin(beta), -sin(alpha)],
		[sin(beta), cos(beta), 0],
		[sin(alpha)*cos(beta), -sin(alpha)*sin(beta), cos(alpha)]
	])
	return U_mag, alpha, beta, C_loc_stab

def lift_drag(CL, CD, rho, A, U_mag, Cbw, r_qc):
	Q = 1/2*rho*U_mag**2
	L = Q*CL*A
	D = Q*CD*A
	F = Cbw @ array([-D, 0, -L])
	M = cross(r_qc, F)
	return L, D, F, M

def load_constants(path_constants, debug=False):
	constants = {}
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
				continue
			key = content[:sep].strip()
			# no key
			if len(key) == 0 or key.isspace():
				print(f'WARNING: line ({line_num}) - blank key for row: {line}')
				continue
			valueStr = content[sep+1:].strip()
			# blank
			if len(valueStr) == 0 or valueStr.isspace():
				print(f'WARNING: line ({line_num}) - blank value for key: {key}')
				continue
			# vector
			if valueStr.startswith('('):
				value = []
				for v in valueStr[1:-1].split(','):
					try:
						value.append(float(v))
					except:
						print(f'WARNING: line ({line_num}) - nonfloat component for vector: {key} = {v}')
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
					continue
			if key in constants:
				print(f"WARNING: line ({line_num}) - repeated entry: {key} = {valueStr} = {constants[key]}")
			constants[key] = value
			if debug:
				print(f'DEBUG: line ({line_num}) - key: {f"{key}":<12}\tvalue: {f"{value}":<12}\tvalueStr: {valueStr}')
	return constants

input_cols = ['Z','Pitch','Roll']
grounded_cols = ['Volume','Area']
floating_cols = ['VCx','VCy','VCz','ACx','ACy','ACz']

def load_volume_area_data(path):
	df = pd.read_csv(path)
	df = df.apply(pd.to_numeric, errors='coerce')
	missing_cols = set(input_cols + grounded_cols + floating_cols) - set(df.columns)
	if missing_cols:
		raise Exception(f'missing column(s) {missing_cols}')
	else:
		return df

def interp_volume_area(df):
	df_grounded = df.dropna(subset=grounded_cols)
	df_floating = df.dropna(subset=floating_cols)
	inputs_grounded = df_grounded[input_cols].values
	inputs_floating = df_floating[input_cols].values
	outputs_grounded = df_grounded[grounded_cols].values
	outputs_floating = df_floating[floating_cols].values
	grounded_linear = LinearNDInterpolator(inputs_grounded, outputs_grounded)
	floating_linear = LinearNDInterpolator(inputs_floating, outputs_floating)
	floating_nearest = NearestNDInterpolator(inputs_floating, outputs_floating)
	return grounded_linear, floating_linear, floating_nearest

def load_aero_coeffs(path):
	cols = ['Alpha','CL','CD']
	df = pd.read_csv(path, sep=r'\s+')
	df = df.apply(pd.to_numeric, errors='coerce')
	missing_cols = list(set(cols) - set(df.columns))
	missing_cols.sort()
	if missing_cols:
		raise Exception(f'missing column(s) {missing_cols}')
	else:
		rows_na = df.isna()
		if rows_na.any().any():
			print(f'WARNING: invalid row(s) in aero coefficients: \n{df[rows_na.any(axis=1)]}')
		df = df.dropna()
		return df[cols].to_numpy()

def load_propulsor_data(path_coeffs):
	cols = ['Beta','C_T^*','C_Q^*']
	df = pd.read_csv(path_coeffs, sep=r'\s+')
	df = df.apply(pd.to_numeric, errors='coerce')
	missing_cols = list(set(cols) - set(df.columns))
	missing_cols.sort()
	if missing_cols:
		raise Exception(f'missing column(s) {missing_cols}')
	else:
		rows_na = df.isna()
		if rows_na.any().any():
			print(f'WARNING: invalid row(s) in propulsor data: \n{df[rows_na.any(axis=1)]}')
		df = df.dropna()
		return df[cols].to_numpy()

def query_volume_area(g_linear, f_linear, f_nearest, query, source):
	grounded = g_linear(query)
	floating = f_linear(query)
	if np.any(np.isnan(floating)):
		floating = f_nearest(query)
		print(f"INFO: {source} parameters using nearest interpolation - [z, pitch, roll] = {query}")
	vol = grounded[0][0]
	area = grounded[0][1]
	if vol < 1e-6 or area < 1e-6:
		return vol, area, zero3, zero3
	if np.any(np.isnan(grounded)):
		print(f"ERROR: {source} parameter interpolation bounds exceeded - [z, pitch, roll] = {query}")
		return vol, area, zero3, zero3
	vol_center = floating[0][0:3]
	area_center = floating[0][3:6]
	return vol, area, vol_center, area_center