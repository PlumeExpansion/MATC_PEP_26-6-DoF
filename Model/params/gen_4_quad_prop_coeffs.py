import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def calc_4_quad_propeller_coeffs(beta, coeff):
	beta = np.atleast_1d(beta)

	k = coeff[:, 0]
	A = coeff[:, [1,3]]
	B = coeff[:, [2,4]]

	beta_matrix = beta[:,None]*k

	cos_matrix = np.cos(beta_matrix)
	sin_matrix = np.sin(beta_matrix)

	C_T_C_Q = (cos_matrix @ A + sin_matrix @ B) @ np.array([[0.01, 0], [0, -0.001]])
	return C_T_C_Q.squeeze()

def load_fourrier_coeffs(path_coeffs):
	cols = ['K','T-A(k)','T-B(k)','Q-A(k)','Q-B(k)']
	try:
		df = pd.read_csv(path_coeffs, sep=r'\s+')
		df = df.apply(pd.to_numeric, errors='coerce')
		missing_cols = list(set(cols) - set(df.columns))
		missing_cols.sort()
		if missing_cols:
			print(f'ERROR: fourier coefficients missing column(s) {missing_cols}')
		else:
			rows_na = df.isna()
			if rows_na.any().any():
				print(f'WARNING: invalid row(s) in fourrier coefficients: \n{df[rows_na.any(axis=1)]}')
			df = df.dropna()
			return df[cols].to_numpy()
	except FileNotFoundError:
		print(f'ERROR: fourier coefficients file not found - "{path_coeffs}"')

def main():
	prop = 'B4-70-14'
	input_file = f'./params/4 quad prop data/fourier coeffs/{prop}.txt'
	output_file = f'./params/4 quad prop data/thrust torque coeffs/{prop}.txt'
	export = False
	plot = True

	f_coeffs = load_fourrier_coeffs(input_file)
	beta = np.linspace(0,2*np.pi,360)
	CT_CQ = calc_4_quad_propeller_coeffs(beta,f_coeffs)

	if export:
		try:
			data = np.concatenate((beta[:,None], CT_CQ), axis=1)
			np.savetxt(output_file, data, header='Beta C_T^* C_Q^*', delimiter=' ',comments='')
			print(f'INFO: successfully wrote {len(beta)} lines to file - "{output_file}"')
		except Exception as e:
			print(f'ERROR: failed to write to file - {e}')

	if plot:
		beta_deg = np.rad2deg(beta)
		plt.plot(beta_deg, CT_CQ[:,0])
		plt.plot(beta_deg, -10*CT_CQ[:,1])
		plt.legend(['$C_T^*$','$-10C_Q^*$'])
		plt.title(prop)
		plt.xlabel('Beta [deg]')
		plt.ylabel(r'$C_T^*$ & $-10C_Q^*$')
		plt.xlim(0, 360)
		plt.ylim(-2.2,1.6)
		plt.xticks(np.linspace(0,360,19))
		plt.yticks(np.linspace(-2.2,1.6,20))
		plt.grid()
		plt.show()

if __name__ == '__main__': main()