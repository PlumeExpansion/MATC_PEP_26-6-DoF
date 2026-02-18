import numpy as np
import matplotlib.pyplot as plt
import numpy.polynomial.polynomial as poly
import math

import gen_4_quad_prop_coeffs as FourQuad

def main():
	path = './params/4 quad prop data/fourier coeffs/B4-70-14.txt'
	KV = 150		# motor speed constant (RPM/V)
	Kt = 0.0689		# motor torque constant (Nm/A)
	I0 = 2.7		# no load current (A)
	R0 = 0.013		# motor resistance (Ω)
	
	rho = 1000
	d = 100

	Ke = 60/(2*np.pi*KV)

	f_coeffs = FourQuad.load_fourrier_coeffs(path)

	V_range = np.linspace(-55, 55, 10)
	beta_range =  np.linspace(0, 2*np.pi, 10) + 0.1*np.pi/180
	
	V_mesh, beta_mesh = np.meshgrid(V_range, beta_range, indexing='ij')
	V_flat = V_mesh.flatten()
	beta_flat = beta_mesh.flatten()
	omega_surf1 = np.zeros((len(V_range), len(beta_range)))
	omega_surf2 = np.zeros((len(V_range), len(beta_range)))

	omega_list = []
	for i,V in enumerate(V_range):
		for j,beta in enumerate(beta_range):
			CT_CQ = FourQuad.calc_4_quad_propeller_coeffs(beta,f_coeffs)
			CQ = CT_CQ[1]
			K1 = 1/2*CQ*rho*(np.pi/4*d**3)*(1+math.tan(beta)**2)*(0.7/2*d**2)
			roots = poly.polyroots([K1/Kt*R0, Ke, math.copysign(I0*R0,K1)-V])
			
			if len(roots) == 1:
				roots = np.append(roots, np.nan)
			elif len(roots) == 0:
				roots = [np.nan, np.nan]
			
			omega_list.append(roots)
			omega_surf1[i,j] = roots[0]
			omega_surf2[i,j] = roots[1]

	omega = np.array(omega_list)

	fig1 = plt.figure(figsize=(12,10))
	ax1 = fig1.add_subplot(projection='3d')
	fig2 = plt.figure(figsize=(12,10))
	ax2 = fig2.add_subplot(projection='3d')

	surf11 = ax1.plot_surface(V_mesh, beta_mesh, omega_surf1.real, cmap='viridis', alpha=0.8)
	surf12 = ax1.plot_surface(V_mesh, beta_mesh, omega_surf2.real, cmap='viridis', alpha=0.8)
	ax1.set_xlabel('Voltage [V]')
	ax1.set_ylabel('Beta [rad]')
	ax1.set_zlabel('Omega [rad/s]')
	ax1.set_title('Real Part')
	fig1.colorbar(surf11, ax=ax1, shrink=0.5, aspect=10)
	
	surf21 = ax2.plot_surface(V_mesh, beta_mesh, omega_surf1.imag, cmap='viridis', alpha=0.8)
	surf22 = ax2.plot_surface(V_mesh, beta_mesh, omega_surf2.imag, cmap='viridis', alpha=0.8)
	ax2.set_xlabel('Voltage [V]')
	ax2.set_ylabel('Beta [rad]')
	ax2.set_zlabel('Omega [rad/s]')
	ax2.set_title('Imaginary Part')
	fig2.colorbar(surf21, ax=ax2, shrink=0.5, aspect=10)

	plt.show()

if __name__ == '__main__': main()