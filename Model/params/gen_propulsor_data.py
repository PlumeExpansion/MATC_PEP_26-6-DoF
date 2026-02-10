import numpy as np
import pandas as pd
from scipy.interpolate import interp1d
from numpy import pi, tan, roots, sign
from itertools import product

def calc_propulsor_data(epsilon, beta, rho, KV, I0, R0, d, CQ_interp):
	K1 = -1800/(pi*KV**2*R0)
	K2 = 30/(pi*KV)*(epsilon/R0-sign(epsilon)*I0)
	K3 = 1/2*CQ_interp(beta)*rho*(pi/4*d**3) * (1+tan(beta)**2)*(0.7*pi*d)**2

	pot_n = roots([-K3, K1, K2])

	print(pot_n)

def load_thrust_torque_coeffs(path_coeffs):
	cols = ['Beta','C_T^*','C_Q^*']
	try:
		df = pd.read_csv(path_coeffs, sep=r'\s+')
		df = df.apply(pd.to_numeric, errors='coerce')
		missing_cols = list(set(cols) - set(df.columns))
		missing_cols.sort()
		if missing_cols:
			print(f'ERROR: thrust torque coefficients missing column(s) {missing_cols}')
		else:
			rows_na = df.isna()
			if rows_na.any().any():
				print(f'WARNING: invalid row(s) in thrust torque coefficients: \n{df[rows_na.any(axis=1)]}')
			df = df.dropna()
			return df[cols].to_numpy()
	except FileNotFoundError:
		print(f'ERROR: thrust torque coefficients file not found - "{path_coeffs}"')

def main():
	prop = 'B4-70-14'
	input_file = f'4 quad prop data/thrust torque coeffs/{prop}.txt'
	# output_file = f'4 quad prop data/thrust torque coeffs/{prop}.txt'

	KV = 150
	I0 = 2.7
	R0 = 0.054
	d = 0.11

	epsilon = 50
	beta = 240
	rho = 1000

	beta_CT_CQ = load_thrust_torque_coeffs(input_file)
	if beta_CT_CQ is None:
		exit()

	CQ_interp = interp1d(beta_CT_CQ[:,0], beta_CT_CQ[:,2], 'cubic')
	calc_propulsor_data(epsilon, np.deg2rad(beta), rho, KV, I0, R0, d, CQ_interp)

if __name__ == '__main__': main()