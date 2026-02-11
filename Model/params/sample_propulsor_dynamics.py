import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp

# --- 1. Motor Parameters (Flipsky 85165 150KV) ---
R = 0.013          	# Resistance (Ohms)
L = 18.2e-6         # Inductance (Henries)
KV = 150            # KV rating (RPM/V)
Kt = 0.0689  		# Torque constant (Nm/A) ≈ 0.0637
Ke = 60 / (2 * np.pi * KV) 		# Back-EMF constant (V/rad/s)
J = 0.00081         # Rotor Inertia (kg*m^2)
I_nl = 2.7          # No-load current (A) - Estimated for this size
W_nl = 382 # No-load speed at 50V (rad/s)

# --- 2. Derived Friction Parameters ---
b = (Kt * I_nl) / W_nl   # Viscous damping coefficient
# tau_f = (Kt * I_nl) * 0.2 # Static friction (estimated at 20% of no-load torque)
# N_smooth = 500           # Smoothing factor for tanh friction

# --- 3. The Nonlinear ODE System ---
def motor_dynamics(t, x, V_func, load_func):
    i, omega = x
    
    # Get time-varying inputs
    V = V_func(t)
    tau_load = load_func(t)
    
    # Electrical: di/dt = (V - R*i - Ke*omega) / L
    didt = (V - R*i - Ke*omega) / L
    
    # Mechanical: dw/dt = (Kt*i - b*omega - friction - load) / J
    # Using tanh to handle the sgn(omega) discontinuity smoothly
    # friction = tau_f * np.tanh(N_smooth * omega)
    friction = 0
    dwdt = (Kt*i - b*omega - friction - tau_load) / J
    
    return [didt, dwdt]

# --- 4. Simulation Scenario Setup ---
def input_voltage(t):
    target_v = 50.0
    start_time = 1
    ramp_duration = 2 # 200ms ramp
    
    if t < start_time:
        return 0
    elif t < start_time + ramp_duration:
        # Linearly ramp from 0 to target_v
        return target_v * (t - start_time) / ramp_duration
    else:
        return max(target_v * (1-(t - start_time - ramp_duration) / ramp_duration),-target_v)

def external_load(t):
    # Apply a 2 Nm load torque halfway through
    # return (2.0 if t < 2 else (-2.0 if t < 8 else 0)) if t > 1 else 0.0
    return 2.0 if t > 1 else 0

# Time span and initial conditions [Current, Speed]
t_span = (0, 10)
# t_eval = np.linspace(0, 1.0, 2000)
x0 = [0, 0]

# --- 5. Run the Integration ---
sol = solve_ivp(motor_dynamics, t_span, x0, 
                args=(input_voltage, external_load), method='RK45')

print(len(sol.t))

# --- 6. Plotting Results ---
fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1, figsize=(10, 8), sharex=True)

# Plot Speed (RPM)
ax1.plot(sol.t, sol.y[1] * 60 / (2 * np.pi), color='blue', lw=2)
ax1.set_ylabel('Speed (RPM)')
ax1.set_title('Nonlinear DC Motor Simulation (Flipsky 85165)')
ax1.grid(True)

# Plot Current (Amps)
ax2.plot(sol.t, sol.y[0], color='black', lw=2)
ax2.set_ylabel('Current (Amps)')
ax2.grid(True)

# Plot Voltage (V)
ax3.plot(sol.t, [input_voltage(t) for t in sol.t], color='red', lw=2)
ax3.set_ylabel('Voltage (V)')
ax3.grid(True)

# Plot Torque (Nm)
ax4.plot(sol.t, [external_load(t) for t in sol.t], color='orange', lw=2)
ax4.set_ylabel('Load (Nm)')
ax4.set_xlabel('Time (seconds)')
ax4.grid(True)

plt.tight_layout()
plt.show()