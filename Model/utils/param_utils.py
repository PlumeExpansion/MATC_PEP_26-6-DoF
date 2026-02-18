import numpy as np
import pandas as pd
from numba import njit

@njit(cache=True)
def clip(val,a,b):
	return max(min(val,b),a)

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
				value = np.array(value)
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

def load_volume_area_data(path_npz):
	data = np.load(path_npz)
	range_z = data['z_range']
	range_pitch = data['pitch_range']
	range_roll = data['roll_range']
	grid_results = data['grid_results']
	
	len_z = len(range_z)
	len_pitch = len(range_pitch)
	len_roll = len(range_roll)

	res_z = (max(range_z) - min(range_z))/len_z
	res_pitch = (max(range_pitch) - min(range_pitch))/len_pitch
	res_roll = (max(range_roll) - min(range_roll))/len_roll
	
	i_max_z = len(range_z) - 2
	i_max_pitch = len(range_pitch) - 2
	i_max_roll = len(range_roll) - 2

	min_base = np.array([min(range_z), min(range_pitch), min(range_roll)])
	res = np.array([res_z, res_pitch, res_roll])

	return grid_results, (range_z,range_pitch,range_roll, res_z,res_pitch,res_roll, 
					   i_max_z,i_max_pitch,i_max_roll, min_base, res)

@njit(cache=True)
def query_volume_area(volume_area, query, r_CM):
	z, pitch, roll = query
	grid_results = volume_area[0]
	(range_z,range_pitch,range_roll, res_z,res_pitch,res_roll, 
  		i_max_z,i_max_pitch,i_max_roll, min_base, res) = volume_area[1]
	i_z, i_pitch, i_roll = ((query-min_base)/res).astype(np.int32)

	i_z = clip(i_z, 0, i_max_z)
	i_pitch = clip(i_pitch, 0, i_max_pitch)
	i_roll = clip(i_roll, 0, i_max_roll)

	d_z = (z - range_z[i_z]) / res_z
	d_pitch = (pitch - range_pitch[i_pitch]) / res_pitch
	d_roll = (roll - range_roll[i_roll]) / res_roll

	c00 = grid_results[i_z][i_pitch][i_roll]*(1-d_z) + grid_results[i_z+1][i_pitch][i_roll]*d_z
	c01 = grid_results[i_z][i_pitch][i_roll+1]*(1-d_z) + grid_results[i_z+1][i_pitch][i_roll+1]*d_z
	c10 = grid_results[i_z][i_pitch+1][i_roll]*(1-d_z) + grid_results[i_z+1][i_pitch+1][i_roll]*d_z
	c11 = grid_results[i_z][i_pitch+1][i_roll+1]*(1-d_z) + grid_results[i_z+1][i_pitch+1][i_roll+1]*d_z

	c0 = c00*(1-d_pitch) + c10*d_pitch
	c1 = c01*(1-d_pitch) + c11*d_pitch

	output = c0*(1-d_roll) + c1*d_roll

	vol = output[0]
	area = output[1]
	if vol < 1e-6 or area < 1e-6:
		return vol, area, np.zeros(3), np.zeros(3)
	vol_center = output[2:5] - r_CM
	area_center = output[5:8] - r_CM
	return vol, area, vol_center, area_center

def load_aero_coeffs(path):
	return load_periodic_1D_data(path, ['Alpha','CL','CD'], 'aerodynamic coefficients')

def load_thrust_torque_coeffs(path):
	return load_periodic_1D_data(path, ['Beta','C_T^*','C_Q^*'], 'propulsor')

def load_periodic_1D_data(path_data, cols, data_name):
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
		data = df[cols].to_numpy()
		length = len(data)
		input_min = min(data[:,0])
		input_max = max(data[:,0])
		period = input_max - input_min
		res = period/length
		return data, (length, input_min, input_max, period, res)

@njit(cache=True)
def query_periodic_1D(periodic_1d,x):
	data = periodic_1d[0]
	length, input_min, input_max, period, res = periodic_1d[1]
	x %= period
	if x >= input_max: x -= period
	i = int((x - input_min) / res)
	dx = (x - data[i][0]) / res
	c0 = data[i][1:]
	c1 = data[i+1 if i+1 < length-1 else 0][1:]
	return c0*(1-dx) + c1*dx

if __name__ == '__main__':
	import matplotlib.pyplot as plt

	# aero_coeffs = load_aero_coeffs('params/sample aero coeffs/wing_1.txt')
	# alpha_range = np.linspace(-360, 360, 514)
	# CL_CD = np.zeros((len(alpha_range),2))
	# for i,alpha in enumerate(alpha_range):
	# 	CL_CD[i] = query_periodic_1D(aero_coeffs, alpha)

	# plt.plot(alpha_range, CL_CD[:,0], label='$C_L$')
	# plt.xlim(min(alpha_range), max(alpha_range))
	# plt.legend()
	# plt.figure()
	# plt.plot(alpha_range, CL_CD[:,1], label='$C_D$')
	# plt.xlim(min(alpha_range), max(alpha_range))
	# plt.legend()
	
	# thrust_torque_coeffs = load_thrust_torque_coeffs('params/4 quad prop data/thrust torque coeffs/B4-70-14.txt')
	# beta_range = np.linspace(-2*np.pi,2*np.pi,524)
	# CT_CQ = np.zeros((len(beta_range), 2))
	# for i,beta in enumerate(beta_range):
	# 	CT_CQ[i] = query_periodic_1D(thrust_torque_coeffs, beta)
	
	# plt.figure()
	# plt.plot(beta_range*np.pi/180, CT_CQ[:,0], label='$C_T^*$')
	# plt.plot(beta_range*np.pi/180, -10*CT_CQ[:,1], label='$C_Q^*$')
	# plt.xlim(min(beta_range*np.pi/180), max(beta_range*np.pi/180))
	# plt.legend()

	vol_area_data = load_volume_area_data('params/hull_data_regular_grid.npz')
	z_range = np.linspace(0,0.2,100)
	vol_area = np.zeros((len(z_range), 2))
	for i,z in enumerate(z_range):
		vol_area[i] = query_volume_area(vol_area_data, np.array([z,0,0]), np.array([0,0,0]))[0:2]

	plt.figure()
	plt.plot(z_range, vol_area[:,0], label='Volume')
	plt.xlim(min(z_range), max(z_range))
	plt.legend()
	plt.figure()
	plt.plot(z_range, vol_area[:,1], label='Area')
	plt.xlim(min(z_range), max(z_range))
	plt.legend()

	plt.show()