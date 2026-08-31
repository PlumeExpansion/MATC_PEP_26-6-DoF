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
		# beta_deg = np.rad2deg(beta)
		# plt.plot(beta_deg, CT_CQ[:,0])
		# plt.plot(beta_deg, -10*CT_CQ[:,1])
		# plt.legend(['$C_T^*$','$-10C_Q^*$'])
		# plt.title(prop)
		# plt.xlabel('Beta [deg]')
		# plt.ylabel(r'$C_T^*$ & $-10C_Q^*$')
		# plt.xlim(0, 360)
		# plt.ylim(-2.2,1.6)
		# plt.xticks(np.linspace(0,360,19))
		# plt.yticks(np.linspace(-2.2,1.6,20))
		# plt.grid()
		# plt.show()

		beta_deg = np.rad2deg(beta)
		fig, ax = plt.subplots(figsize=(10, 6))

		# Quadrant Definitions from Table 3
		quadrants = [
			{'num': 1, 'name': 'Ahead', 'start': 0, 'end': 90, 'color': '#e6f2ff'},
			{'num': 2, 'name': 'Crashback', 'start': 90, 'end': 180, 'color': '#ffffff'},
			{'num': 3, 'name': 'Backing', 'start': 180, 'end': 270, 'color': '#e6f2ff'},
			{'num': 4, 'name': 'Crashahead', 'start': 270, 'end': 360, 'color': '#ffffff'}
		]

		# Plot quadrant background shading and labels
		for q in quadrants:
			ax.axvspan(q['start'], q['end'], color=q['color'], alpha=0.5, zorder=0)
			ax.text((q['start'] + q['end']) / 2, 1.9, f"Q{q['num']}\n{q['name']}", 
			        ha='center', va='top', fontsize=10, fontweight='bold',
			        bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8, edgecolor='none'))
			if q['start'] > 0:
				ax.axvline(q['start'], color='gray', linestyle='--', linewidth=0.8, alpha=0.7)

		# Plot coefficients
		ax.plot(beta_deg, CT_CQ[:,0], label=r'$C_T^*$', linewidth=1.8)
		ax.plot(beta_deg, -10*CT_CQ[:,1], label=r'$-10C_Q^*$', linewidth=1.8)

		ax.set_title(f'4-Quadrant Propeller Model: {prop}', fontsize=12, pad=15)
		ax.set_xlabel(r'Beta $\beta$ [deg]')
		# ax.set_ylabel(r'$C_T^*$ & $-10C_Q^*$')
		ax.set_ylabel('Non-dimensional Thrust & Torque Coefficients')
		ax.set_xlim(0, 360)
		ax.set_ylim(-2.2, 2.0)
		ax.set_xticks(np.linspace(0, 360, 19))
		ax.set_yticks(np.linspace(-2.2, 2.0, 22))
		ax.legend(loc='lower left')
		ax.grid(True, linestyle=':', alpha=0.6)
		
		plt.tight_layout()
		plt.show()

if __name__ == '__main__': main()