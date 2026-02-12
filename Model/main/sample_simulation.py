from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt

from utils import *
import model_RBird

model = model_RBird.make_default()

def get_state_dots(t, states):
	inputs = get_inputs(t)

	model.set_state(states[0:12])
	model.set_input(inputs[0])
	model.propulsor.set_state(states[12:])
	model.propulsor.set_input(inputs[1])

	model.calc_state_dot()
	model.propulsor.calc_state_dot()

	return concatenate((model.get_state_dot(), model.propulsor.get_state_dot()))

def get_inputs(t):
	return zeros(2)

t_span = (0, 10)
states0 = concatenate((model.get_state(), model.propulsor.get_state()))

sol = solve_ivp(fun=get_state_dots, t_span=t_span, y0=states0, method='RK45')

# Extract results and plot
U = sol.y[0:3]
omega = sol.y[3:6]
Phi = sol.y[6:9]
r = sol.y[9:12]

I = sol.y[12]
omega = sol.y[13]

inputs = get_inputs(sol.t)

for (i, name) in enumerate(['u','v','w']):
	plt.subplot(3,3,i)
	plt.plot(sol.t, U[i])
	plt.legend(name)
	plt.grid()

for (i, name) in enumerate(['p','q','r']):
	plt.subplot(3,3,i+3)
	plt.plot(sol.t, omega[i])
	plt.legend(name)
	plt.grid()

for (i, name) in enumerate([r'$\phi$',r'$\theta$',r'$\psi$']):
	plt.subplot(3,3,i+6)
	plt.plot(sol.t, Phi[i])
	plt.legend(name)
	plt.grid()

plt.suptitle('6DoF States')

plt.figure()
plt.subplot(2,1,1)
plt.plot(sol.t, I)
plt.legend('I')
plt.grid

plt.subplot(2,1,2)
plt.plot(sol.t, omega)
plt.legend(r'$\omega$')
plt.grid

plt.suptitle('Propulsor States')

plt.figure()
plt.subplot(2,1,1)
plt.plot(sol.t, inputs[0])
plt.legend(r'$\psi_{ra}$')
plt.grid

plt.subplot(2,1,1)
plt.plot(sol.t, inputs[1])
plt.legend(r'$\epsilon$')
plt.grid

plt.suptitle('Inputs')

plt.show()