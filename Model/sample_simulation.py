from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt
import time

from components.utils import *
import model_RBird

model = model_RBird.make_default()

def get_state_dots(t, states):
	model.set_state(states)
	model.set_input(get_inputs(t))
	model.calc_state_dot()
	return model.get_state_dot()

def get_inputs(t):
	return np.zeros(2)

t_span = (0, 10)
states0 = model.get_state()

print('INFO: solving ODE...')
tik = time.perf_counter()
sol = solve_ivp(fun=get_state_dots, t_span=t_span, y0=states0, method='RK45')
tok = time.perf_counter()-tik
if sol.success:
	print(f'INFO: solved for t = {t_span} with {len(sol.t)} steps in {tok:.2f} seconds')
else:
	print(f'ERROR: solver failed - "{sol.message}" - elasped: {tok:.2f} seconds, exiting')
	exit()

PLOT = True

if PLOT:
	# Extract results and plot
	U = sol.y[0:3,:]
	omega = sol.y[3:6,:]
	Phi = sol.y[6:9,:]
	r = sol.y[9:12,:]

	I = sol.y[12,:]
	omega_p = sol.y[13,:]

	inputs = np.zeros((len(sol.t),2))
	for i,t in enumerate(sol.t):
		inputs[i] = get_inputs(t)

	for (i, name) in enumerate(['u','v','w']):
		plt.subplot(4,3,i+1)
		plt.plot(sol.t, U[i,:])
		plt.legend(name)
		plt.grid()

	for (i, name) in enumerate(['p','q','r']):
		plt.subplot(4,3,i+4)
		plt.plot(sol.t, omega[i,:])
		plt.legend(name)
		plt.grid()

	for (i, name) in enumerate([r'$\phi$',r'$\theta$',r'$\psi$']):
		plt.subplot(4,3,i+7)
		plt.plot(sol.t, Phi[i,:])
		plt.legend([name])
		plt.grid()

	for (i, name) in enumerate(['x','y','z']):
		plt.subplot(4,3,i+10)
		plt.plot(sol.t, r[i,:])
		plt.legend(name)
		plt.grid()

	plt.suptitle('6DoF States')

	plt.figure()
	plt.subplot(2,1,1)
	plt.plot(sol.t, I)
	plt.legend('I')
	plt.grid()

	plt.subplot(2,1,2)
	plt.plot(sol.t, omega_p)
	plt.legend([r'$\omega$'])
	plt.grid()

	plt.suptitle('Propulsor States')

	plt.figure()
	plt.subplot(2,1,1)
	plt.plot(sol.t, inputs[:,0])
	plt.legend([r'$\psi_{ra}$'])
	plt.grid()

	plt.subplot(2,1,2)
	plt.plot(sol.t, inputs[:,1])
	plt.legend([r'$\epsilon$'])
	plt.grid()

	plt.suptitle('Inputs')

	plt.show()