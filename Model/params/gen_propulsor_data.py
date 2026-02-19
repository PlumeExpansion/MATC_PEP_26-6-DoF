import numpy as np
import matplotlib.pyplot as plt
import math
import time

from scipy.interpolate import griddata

import gen_4_quad_prop_coeffs as FourQuad

def main():
	prop_path = './params/4 quad prop data/fourier coeffs/B4-70-14.txt'
	KV = 150		# motor speed constant (RPM/V)
	Kt = 0.0689		# motor torque constant (Nm/A)
	I0 = 2.7		# no load current (A)
	R0 = 0.013		# motor resistance (Ω)

	d = 0.1			# propeller diameter (m)
	
	output_path = f'./params/propulsor data/FlipSky-85165-150_B4-70-14_{int(d*100)}.npz'

	raw_v_val = 25		
	raw_V_max = 60

	export_v_val = 20
	export_V_max = 55
	
	Ke = 60/(2*np.pi*KV)
	n_max = KV*raw_V_max/60

	plot_raw = True
	plot_interp = False
	export = False

	f_coeffs = FourQuad.load_fourrier_coeffs(prop_path)

	pos_n_range = np.concatenate((np.arange(0,0.1,0.01),np.arange(0.1,1,0.1),np.arange(1,5,1),np.arange(5,30,2),np.arange(30,50,2.5),np.arange(50,n_max,5)))
	n_range = np.concatenate((-1*np.flip(pos_n_range),pos_n_range))
	beta_range =  np.linspace(0, 2*np.pi, 361)
	rho_range = np.array([0.8, 1.4, 995, 1100])
	
	X_surf = np.zeros((len(n_range), len(beta_range), len(rho_range)))
	Y_surf = np.zeros((len(n_range), len(beta_range), len(rho_range)))
	Z_surf = np.zeros((len(n_range), len(beta_range), len(rho_range)))
	W_surf = np.zeros((len(n_range), len(beta_range), len(rho_range)))

	tik = time.perf_counter_ns()
	for i,n in enumerate(n_range):
		v_rot = 0.7*np.pi*n*d
		beta_val = math.atan2(raw_v_val,math.fabs(v_rot))
		for j,beta in enumerate(beta_range):
			CT_CQ = FourQuad.calc_4_quad_propeller_coeffs(beta,f_coeffs)
			CQ = CT_CQ[1]
			v_A = math.tan(beta)*v_rot
			valid = True
			if n == 0:
				valid = False
			elif n > 0:
				valid = not (beta_val < beta < 2*np.pi-beta_val)
			else:
				valid = math.fabs(beta - np.pi) < beta_val
				
			if valid:
				for k,rho in enumerate(rho_range):
					Q = 1/2*CQ*rho*(np.pi/4*d**3)*(1+math.tan(beta)**2)*v_rot**2
					I = Q/Kt + math.copysign(I0, Kt)
					V = I*R0 + Ke*(2*np.pi*n)

					X_surf[i,j,k] = v_A
					Y_surf[i,j,k] = V
					Z_surf[i,j,k] = rho
					W_surf[i,j,k] = n
			else:
				X_surf[i,j,:] = np.full((1,len(rho_range)), np.nan)
				Y_surf[i,j,:] = np.full((1,len(rho_range)), np.nan)
				Z_surf[i,j,:] = np.full((1,len(rho_range)), np.nan)
				W_surf[i,j,:] = np.full((1,len(rho_range)), np.nan)
	tok = time.perf_counter_ns()
	print(f'INFO: finished calculating in {(tok-tik)/10e9:.2f} s')
	tik = tok

	mask = ~np.isnan(X_surf)
	points = np.column_stack((X_surf[mask], Y_surf[mask], Z_surf[mask]))
	values = W_surf[mask]

	va_lookup = np.linspace(-export_v_val, export_v_val, 100)
	V_lookup = np.linspace(-export_V_max, export_V_max, 100)
	vA_grid, V_grid, rho_grid = np.meshgrid(va_lookup, V_lookup, rho_range)

	n_lookup = griddata(points, values, (vA_grid, V_grid, rho_grid), method='linear')

	tok = time.perf_counter_ns()
	print(f'INFO: finished interpolating in {(tok-tok)/10e9:.2f} s')

	if export:
		try:
			np.savez(output_path, n=n_lookup, va=va_lookup, V=V_lookup, rho=rho_range)
			print(f'INFO: Successfully exported to "{output_path}"')
		except Exception as e:
			print(f'ERROR: Failed to export - {e}')

	if plot_interp:
		plt.figure()
		plt.pcolormesh(vA_grid, V_grid, n_lookup[:,:,2], shading='auto', cmap='magma')
		plt.colorbar(label='Rotational Speed $n$ [rev/s]')
		plt.xlabel('$v_A$ [m/s]')
		plt.ylabel('Voltage $V$ [V]')
		plt.title('Interpolated Operating Speed: $n = f(v_A, V)$')
		plt.show()

	if plot_raw:
		fig = plt.figure(figsize=(12,8))
		ax = fig.add_subplot(projection='3d')

		surf = ax.plot_surface(X_surf[:,:,2], Y_surf[:,:,2], W_surf[:,:,2], cmap='viridis', alpha=0.8, axlim_clip=True)
		ax.set_xlabel('$v_A$ [m/s] (Advance Velocity)')
		ax.set_ylabel('Voltage $V$ [V]')
		ax.set_zlabel('Rotational Speed $n$ [rev/s]')
		ax.set_title('Propulsor Operating Speed')

		ax.set_xlim([-raw_v_val, raw_v_val])
		ax.set_ylim([-raw_V_max, raw_V_max])

		fig.colorbar(surf, ax=ax, shrink=0.5, aspect=10)

	plt.show()

if __name__ == '__main__': main()