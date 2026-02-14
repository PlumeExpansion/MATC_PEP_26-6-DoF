import numpy as np
import pandas as pd
import numpy.linalg as LA
import cProfile
import pstats
from scipy.interpolate import RegularGridInterpolator
import math
# from numba import njit
from math import (pi, cos, sin, atan2, asin, acos, sqrt)
from numpy import (transpose, roots, array, eye, zeros, ones, concatenate)

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

# @njit(cache=True)
def sign(v):
	return -1 if v < 0 else 1

# @njit(cache=True)
def unit(vec):
	return vec / mag(vec)

# @njit(cache=True)
def mag(vec):
	return sqrt(vec[0]**2 + vec[1]**2 + vec[2]**2)

# @njit(cache=True)
def cross(a, b):
	return array([
		a[1]*b[2] - a[2]*b[1],
		a[2]*b[0] - a[0]*b[2],
		a[0]*b[1] - a[1]*b[0]
	])

# @njit(cache=True)
def clip(v,a,b):
	return max(min(v,b),a)

# @njit(cache=True)
def stab_frame(U, omega, X, C_loc_ref):
	U_local = U + cross(omega, X)
	U_local_loc_frame = C_loc_ref @ U_local
	U_mag = mag(U_local)
	if U_mag < 1e-6:
		return U_mag, 0, 0, eye3
	alpha = atan2(U_local_loc_frame[2], U_local[0])
	beta = asin(U_local_loc_frame[1] / U_mag)
	ca, sa = cos(alpha), sin(alpha)
	cb, sb = cos(beta), sin(beta)
	C_loc_stab = array([
		[ca*sb, -ca*sb, -sa],
		[sb, cb, 0],
		[sa*cb, -sa*sb, ca]
	])
	return U_mag, alpha, beta, C_loc_stab

# @njit(cache=True)
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

class VolumeAreaData:
	def __init__(self, path_npz):
		self.data = np.load(path_npz)
		self.range_z = self.data['z_range']
		self.range_pitch = self.data['pitch_range']
		self.range_roll = self.data['roll_range']
		self.grid_results = self.data['grid_results']
		
		self.len_z = len(self.range_z)
		self.len_pitch = len(self.range_pitch)
		self.len_roll = len(self.range_roll)

		self.res_z = (max(self.range_z) - min(self.range_z))/self.len_z
		self.res_pitch = (max(self.range_pitch) - min(self.range_pitch))/self.len_pitch
		self.res_roll = (max(self.range_roll) - min(self.range_roll))/self.len_roll
		
		self.i_max_z = len(self.range_z) - 2
		self.i_max_pitch = len(self.range_pitch) - 2
		self.i_max_roll = len(self.range_roll) - 2

		self.min_base = np.array([min(self.range_z), min(self.range_pitch), min(self.range_roll)])
		self.res = np.array([self.res_z, self.res_pitch, self.res_roll])
	
	# @njit(cache=True)
	def __int_query(self, i_z, i_pitch, i_roll):
		return self.grid_results[i_z][i_pitch][i_roll]

	# @njit(cache=True)
	def query(self, query):
		z, pitch, roll = query
		i_z, i_pitch, i_roll = ((query-self.min_base)/self.res).astype(int)

		i_z = clip(i_z, 0, self.i_max_z)
		i_pitch = clip(i_pitch, 0, self.i_max_pitch)
		i_roll = clip(i_roll, 0, self.i_max_roll)

		d_z = (z - self.range_z[i_z]) / self.res_z
		d_pitch = (pitch - self.range_pitch[i_pitch]) / self.res_pitch
		d_roll = (roll - self.range_roll[i_roll]) / self.res_roll

		c00 = self.__int_query(i_z,i_pitch,i_roll)*(1-d_z) + self.__int_query(i_z+1,i_pitch,i_roll)*d_z
		c01 = self.__int_query(i_z,i_pitch,i_roll+1)*(1-d_z) + self.__int_query(i_z+1,i_pitch,i_roll+1)*d_z
		c10 = self.__int_query(i_z,i_pitch+1,i_roll)*(1-d_z) + self.__int_query(i_z+1,i_pitch+1,i_roll)*d_z
		c11 = self.__int_query(i_z,i_pitch+1,i_roll+1)*(1-d_z) + self.__int_query(i_z+1,i_pitch+1,i_roll+1)*d_z

		c0 = c00*(1-d_pitch) + c10*d_pitch
		c1 = c01*(1-d_pitch) + c11*d_pitch

		output = c0*(1-d_roll) + c1*d_roll

		vol = output[0]
		area = output[1]
		if vol < 1e-6 or area < 1e-6:
			return vol, area, zero3, zero3
		vol_center = output[0:3]
		area_center = output[3:6]
		return vol, area, vol_center, area_center

def load_aero_coeffs(path):
	return Periodic1D(load_1D_data(path, ['Alpha','CL','CD'], 'aerodynamic coefficients'))

def load_thrust_torque_coeffs(path):
	return Periodic1D(load_1D_data(path, ['Beta','C_T^*','C_Q^*'], 'propulsor'))

class Periodic1D:
	def __init__(self, data):
		self.data = data
		self.len = len(self.data)
		self.min = min(self.data[:,0])
		self.max = max(self.data[:,0])
		self.period = self.max - self.min
		self.res = self.period/self.len
	
	# @njit(cache=True)
	def query(self, x):
		x %= self.period
		if x >= self.max: x -= self.period
		i = int((x - self.min) / self.res)
		dx = (x - self.data[i][0]) / self.res
		c0 = self.data[i][1:]
		c1 = self.data[i+1 if i+1 < self.len-1 else 0][1:]
		return c0*(1-dx) + c1*dx

def load_1D_data(path_data, cols, data_name):
	df = pd.read_csv(path_data, sep=r'\s+')
	df = df.apply(pd.to_numeric, errors='coerce')
	missing_cols = list(set(cols) - set(df.columns))
	missing_cols.sort()
	if missing_cols:
		raise Exception(f'missing column(s) {missing_cols}')
	else:
		rows_na = df.isna()
		if rows_na.any().any():
			print(f'WARNING: invalid row(s) in {data_name} data: \n{df[rows_na.any(axis=1)]}')
		df = df.dropna()
		return df[cols].to_numpy()

if __name__ == '__main__':
	import matplotlib.pyplot as plt

	aero_coeffs = load_aero_coeffs('params/sample aero coeffs/wing_1.txt')
	alpha_range = np.linspace(-360, 360, 514)
	CL_CD = np.zeros((len(alpha_range),2))
	for i,alpha in enumerate(alpha_range):
		CL_CD[i] = aero_coeffs.query(alpha)

	plt.plot(alpha_range, CL_CD[:,0], label='$C_L$')
	plt.xlim(min(alpha_range), max(alpha_range))
	plt.legend()
	plt.figure()
	plt.plot(alpha_range, CL_CD[:,1], label='$C_D$')
	plt.xlim(min(alpha_range), max(alpha_range))
	plt.legend()
	
	thrust_torque_coeffs = load_thrust_torque_coeffs('params/4 quad prop data/thrust torque coeffs/B4-70-14.txt')
	beta_range = np.linspace(-2*pi,2*pi,524)
	CT_CQ = np.zeros((len(beta_range), 2))
	for i,beta in enumerate(beta_range):
		CT_CQ[i] = thrust_torque_coeffs.query(beta)
	
	plt.figure()
	plt.plot(beta_range*pi/180, CT_CQ[:,0], label='$C_T^*$')
	plt.plot(beta_range*pi/180, -10*CT_CQ[:,1], label='$C_Q^*$')
	plt.xlim(min(beta_range*pi/180), max(beta_range*pi/180))
	plt.legend()

	plt.show()
