import numpy as np
import matplotlib.pyplot as plt
import time

from scipy.optimize import brentq

import gen_4_quad_prop_coeffs as FourQuad

def main():
	prop_path = './params/4 quad prop data/fourier coeffs/B4-70-14.txt'
	KV = 150		# motor speed constant (RPM/V)
	Kt = 0.0689		# motor torque constant (Nm/A)
	I0 = 2.7		# no load current (A)
	R0 = 0.0582		# motor resistance (Ω)

	d = 0.12		# propeller diameter (m)
	d_h = 0.085		# hub diameter (m)

	f_d0 = 0.167	# standard tip-to-tip to hub diameter ratop
	
	output_path = f'./params/propulsor data/FlipSky-85165-150_B4-70-14_{int(d*100)}.npz'
	
	Ke = 60/(2*np.pi*KV)
	f_d = d_h/d
	eta_T_h = (1-f_d**2)/(1-f_d0**2)

	print(f'INFO: thrust deduction factor - {eta_T_h}')

	plot = False
	plot_idx = 3		# n,T,Q,I
	calculate = True

	rho_range = np.array([0.8, 1.4, 995, 1100])
	vA_range = np.linspace(-20,20,100)
	V_range = np.linspace(-55,55,100)

	if calculate:
		f_coeffs = FourQuad.load_fourrier_coeffs(prop_path)

		n_max = 55*KV/60

		table = np.zeros((len(rho_range), len(vA_range), len(V_range), 4))

		tik = time.perf_counter_ns()
		
		def get_params(n, rho,vA):
			vRot = 0.7*np.pi*n*d
			vR2 = vRot**2 + vA**2
			beta = np.atan2(vA,vRot+1e-6)
			CT_CQ = FourQuad.calc_4_quad_propeller_coeffs(beta, f_coeffs)
			if CT_CQ.ndim == 1:
				T = 1/2*CT_CQ[0]*rho*(np.pi/4*d**2)*vR2 * eta_T_h
				Q = 1/2*CT_CQ[1]*rho*(np.pi/4*d**3)*vR2
			else:
				T = 1/2*CT_CQ[:,0]*rho*(np.pi/4*d**2)*vR2 * eta_T_h
				Q = 1/2*CT_CQ[:,1]*rho*(np.pi/4*d**3)*vR2
			# I = Q/Kt + I0*np.tanh(Q / 1)
			I = Q/Kt + np.copysign(I0, Q)

			return np.array([T,Q,I])
			# return res.flatten() if np.isscalar(n) else res

		def residual(n, rho,vA,V):
			_,_,I = get_params(n, rho,vA)
			# rotation speed residual
			# n_calc = (V-I*R0)/(Ke*2*np.pi)
			# return n_calc - n
			# current residual
			I_calc = (V-Ke*2*np.pi*n)/R0
			return I_calc-I

		for i,rho in enumerate(rho_range):
			for j,vA in enumerate(vA_range):
				for k,V in enumerate(V_range):
					try:
						sol = brentq(lambda n: residual(n, rho,vA,V), -n_max, n_max)
						table[i,j,k,0] = sol # type: ignore
					except ValueError:
						table[i,j,k,0] = V/(Ke*2*np.pi)
						print(f'ERROR: failed to converge at rho={rho:<10.1f}vA={vA:<10.2f}V={V}')
				n_sol_vec = table[i,j,:,0]
				table[i,j,:,1:4] = get_params(n_sol_vec, rho,vA).T # type: ignore

		tok = time.perf_counter_ns()
		print(f'INFO: finished calculating in {(tok-tik)/10e9:.2f} s')

		try:
			np.savez(output_path, grid_results=table, rho_range=rho_range, vA_range=vA_range, V_range=V_range, d=d)
			print(f'INFO: Successfully exported to "{output_path}"')
		except Exception as e:
			print(f'ERROR: Failed to export - {e}')

	if plot:
		table = np.load(output_path)['grid_results']
		for i,rho in enumerate(rho_range):
			vA_grid, V_grid = np.meshgrid(vA_range, V_range, indexing='ij')

			lbl = ['Rotation Speed $n$ [rev/s]','Thrust $T$ [N]','Torque $Q$ [Nm]','Current $I$ [A]'][plot_idx]

			plt.figure()
			plt.pcolormesh(vA_grid, V_grid, table[i,:,:,plot_idx], shading='auto', cmap='magma')
			plt.colorbar(label=lbl)
			plt.xlabel('$v_A$ [m/s]')
			plt.ylabel('Voltage $V$ [V]')
			plt.title(f'{lbl} ($rho$={rho})')
		
		plt.show()

if __name__ == '__main__': 
	try:
		main()
	except KeyboardInterrupt:
		plt.close('all')
		print('INFO: exiting')