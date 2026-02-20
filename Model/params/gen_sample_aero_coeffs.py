import numpy as np
import matplotlib.pyplot as plt
from numpy import linspace, pi, exp, sin, abs, pow, deg2rad
from collections import namedtuple

def gen_sample_lift_coeff(alpha, CL0, CLalpha, alpha_crit, CLrec):
	CL1 = CL0 + CLalpha*alpha
	CL2 = CLrec*sin(deg2rad(2*alpha))
	f = (1+exp(-0.4*(abs(alpha) - 1.2*alpha_crit)))**-1
	CL = CL1*(1-f) + f*CL2
	return CL

def gen_sample_drag_coeff(alpha, CD0, CDtrans, alpha_trans, CDmax):
	CDi = lambda alpha: pow(abs(alpha), 4)
	k = (CDtrans-CD0)/CDi(alpha_trans)
	CD1 = CD0 + k*CDi(alpha)
	CD2 = CDmax*sin(deg2rad(alpha))**2
	f = (1+exp(-0.18*(abs(alpha) - 1.5*alpha_trans)))**-1
	CD = CD1*(1-f) + f*CD2
	return CD

# Blended Lift & Drag: https://www.desmos.com/calculator/qsqemsi5d9

def main():
	FoilParams = namedtuple('FoilParams', ['id','CL0','CLalpha','alpha_crit','CLrec','CD0','CDtrans','alpha_trans','CDmax'])
	alpha = linspace(-180, 180, 360)
	wr = FoilParams('wing_root',	0.0, 0.1, 10, 1,	0.02, 0.1, 20, 2)		# (e479-il)
	wv = FoilParams('wing_v',	0.0, 0.12, 10, 1,	0.01, 0.12, 15, 2)		# (b540ols-il)
	w1 = FoilParams('wing_1',	0.3, 0.15, 10, 1,	0.01, 0.1, 15, 2)		# (hq209-il)
	w2 = FoilParams('wing_2',	0.2, 0.14, 10, 1,	0.01, 0.06, 15, 2)		# (ag04-il)
	w3 = FoilParams('wing_3',	0.0, 0.11, 8, 1,	0.01, 0.1, 10, 2)		# (ea81006-il)
	
	wr1 = FoilParams('wing_r1',	0.1, 0.11, 7, 1,	0.007, 0.07, 10, 2)		# (ag47ct02r-il)
	wr2 = FoilParams('wing_r2',	0.1, 0.11, 7, 1,	0.007, 0.07, 10, 2)		# (ag47ct02r-il)
	wrv = FoilParams('wing_rv',	0.0, 0.1, 6, 1,		0.007, 0.07, 8, 2)		# (goe445-il)
	wrs = FoilParams('wing_rs',	0.0, 0.1, 6, 1,		0.007, 0.07, 8, 2)		# (goe445-il)
	
	h = FoilParams('hull',		0.25, 0.06, 5, 1,	0.1, 0.14, 12, 1.5)		# streamlined half body
	s = FoilParams('surf',		0.0, 0.06, 5, 1,	0.05, 0.06, 10, 1.5)	# streamlined body

	root = './sample aero coeffs/'
	export = True
	plot = False

	# foils = [wr,wv,w1,w2,w3, wr1,wr2,wrv,wrs,h,s]
	foils = [h]
	for params in foils:
		CL = gen_sample_lift_coeff(alpha, params.CL0, params.CLalpha, params.alpha_crit, params.CLrec)
		CD = gen_sample_drag_coeff(alpha, params.CD0, params.CDtrans, params.alpha_trans, params.CDmax)

		if export:
			data = np.vstack((alpha,CL,CD)).T
			output_file = root + params.id + '_sample_coeffs.txt'
			np.savetxt(output_file, data, header='Alpha CL CD', delimiter=' ',comments='')
			print(f'INFO: successfully wrote {len(alpha)} lines to file - "{output_file}"')

		if plot:
			fig, ax = plt.subplots(1, 2, figsize=(10, 4))
			fig.suptitle(params.id)
			ax[0].plot(alpha, CL, color='blue', label='Lift')
			ax[0].set_ylabel('$C_L$')
			ax[0].set_xlabel('alpha [deg]')
			ax[0].grid(True)
			ax[0].set_xlim(-180, 180)

			ax[1].plot(alpha, CD, color='red', label='Drag')
			ax[1].set_ylabel('$C_D$')
			ax[1].set_xlabel('alpha [deg]')
			ax[1].grid(True)
			ax[1].set_xlim(-180, 180)

			plt.tight_layout()

	if plot:
		plt.show()

if __name__ == '__main__': main()