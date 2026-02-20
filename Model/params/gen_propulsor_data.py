import numpy as np
import matplotlib.pyplot as plt
import time

from scipy.optimize import fsolve

import gen_4_quad_prop_coeffs as FourQuad

def main():
	prop_path = './params/4 quad prop data/fourier coeffs/B4-70-14.txt'
	KV = 150		# motor speed constant (RPM/V)
	Kt = 0.0689		# motor torque constant (Nm/A)
	I0 = 2.7		# no load current (A)
	R0 = 0.013		# motor resistance (Ω)

	d = 0.12		# propeller diameter (m)
	
	output_path = f'./params/propulsor data/FlipSky-85165-150_B4-70-14_{int(d*100)}.npz'
	
	Ke = 60/(2*np.pi*KV)

	plot = False
	export = True

	f_coeffs = FourQuad.load_fourrier_coeffs(prop_path)

	rho_range = np.array([0.8, 1.4, 995, 1100])
	vA_range = np.linspace(-20,20,100)
	V_range = np.linspace(-55,55,100)

	table = np.zeros((len(rho_range), len(vA_range), len(V_range), 4))

	tik = time.perf_counter_ns()
	
	def get_params(n, rho,vA):
		vRot = 0.7*np.pi*n*d
		vR2 = vRot**2 + vA**2
		beta = np.atan2(vA,vRot+1e-6)
		CT_CQ = FourQuad.calc_4_quad_propeller_coeffs(beta, f_coeffs)
		T = 1/2*CT_CQ[:,0]*rho*(np.pi/4*d**2)*vR2
		Q = 1/2*CT_CQ[:,1]*rho*(np.pi/4*d**3)*vR2
		I = Q/Kt + np.copysign(I0, Q)

		return np.array([T,Q,I])

	def residual(n, rho,vA,V):
		_,_,I = get_params(n, rho,vA)
		n_calc = (V-I*R0)/(Ke*2*np.pi)
		return n_calc - n

	for i,rho in enumerate(rho_range):
		for j,vA in enumerate(vA_range):
			vA_vec = np.full(V_range.shape, vA)
			n_guess = V_range/(Ke*2*np.pi)
			sol = fsolve(residual, n_guess, args=(rho,vA_vec,V_range))
			table[i,j, :,0] = sol # type: ignore
			table[i,j, :,1:4] = get_params(sol, rho,vA).T # type: ignore

	tok = time.perf_counter_ns()
	print(f'INFO: finished calculating in {(tok-tik)/10e9:.2f} s')

	if export:
		try:
			np.savez(output_path, grid_results=table, rho_range=rho_range, vA_range=vA_range, V_range=V_range)
			print(f'INFO: Successfully exported to "{output_path}"')
		except Exception as e:
			print(f'ERROR: Failed to export - {e}')

	if plot:
		for i,rho in enumerate(rho_range):
			vA_grid, V_grid = np.meshgrid(vA_range, V_range, indexing='ij')

			plt.figure()
			plt.pcolormesh(vA_grid, V_grid, table[i,:,:,0], shading='auto', cmap='magma')
			plt.colorbar(label='Rotational Speed $n$ [rev/s]')
			plt.xlabel('$v_A$ [m/s]')
			plt.ylabel('Voltage $V$ [V]')
			plt.title(f'Propulsor Operating Speed ($rho$={rho})')
		
		plt.show()

if __name__ == '__main__': main()