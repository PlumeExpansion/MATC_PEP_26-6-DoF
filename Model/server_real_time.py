import asyncio
import websockets
import json
import time
import numpy as np
from scipy.integrate import ode

import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
os.environ['PYTHONWARNINGS'] = 'ignore'
import pygame

import model_RBird as model_RB
from model_RBird import Model_6DoF

# --- Simulation Logic ---
class Simulation:
	def __init__(self, model: Model_6DoF):
		self.model = model
		
		def get_state_dot(t, state):
			self.model.set_state(state)
			return self.model.get_state_dot()

		self.system = ode(get_state_dot).set_integrator('dopri5')
		self.system.set_initial_value(model.get_state())

		self.time_last = 0
		self.pause()

		self.model.calc_state_dot()
		self.__set_build_telem()
		self.__init_telem()
		self.set_telemetry()

	def pause(self):
		self.__running = False

	def resume(self):
		self.__running = True
		self.time_last = time.perf_counter()

	def is_running(self):
		return self.__running

	def reset(self):
		self.pause()
		self.model.set_state(np.zeros(14))
		self.system.set_initial_value(self.model.get_state())
		self.model.set_input(np.zeros(2))
		self.model.calc_state_dot()
		self.set_telemetry()

	def step(self,dt: float=np.nan):
		if self.__running:
			if not np.isnan(dt):
				print('WARNING: simulation step of {dt} requested while running')
			time_now = time.perf_counter()
			dt = time_now - self.time_last
			self.time_last = time_now
		elif np.isnan(dt):
			return
		if self.system.successful():
			self.system.integrate(self.system.t + dt)
			self.model.set_state(self.system.y)
		else:
			self.pause()
			print('ERROR: simulation integration failed, pausing')

	def get_dt(self):
		return time.perf_counter()-self.time_last
	
	def __set_build_telem(self):
		panel_telems = {}
		for panel in self.model.panels.values():
			panel_telems[panel.id] = {
				'rear': panel.rear,
				'r_LE_1': panel.r_LE_1.tolist(),
				'r_LE_2': panel.r_LE_2.tolist(),
				'r_TE_1': panel.r_TE_1.tolist(),
				'r_TE_2': panel.r_TE_2.tolist()
			}
		self.__build_telem = {
			'type': 'build',
			'r_CM': self.model.r_CM.tolist(), # type: ignore
			'r_ra': self.model.r_ra.tolist(), # type: ignore
			'hull': {
				'r_surf': self.model.hull.r_surf.tolist() # type: ignore
			},
			'panels': panel_telems,
			'propulsor': {
				'r_prop': self.model.propulsor.r_prop.tolist(), # type: ignore
				'd': self.model.propulsor.d
			}
		}
		self.build_telem = json.dumps(self.__build_telem)

	def __init_telem(self):
		panel_telems = {}
		for panel in self.model.panels.values():
			panel_telems[panel.id] = {}
		self.__telem = {
			'type': 'telem',
			'hull': {
				'surf': {}
			},
			'panels': panel_telems,
			'wing_roots': {
				'0': {},
				'1': {}
			},
			'propulsor': {}
		}
		self.telem = json.dumps(self.__telem)

	def set_telemetry(self):
		for panel in self.model.panels.values():
			panel_telem = self.__telem['panels'][panel.id]
			panel_telem['alpha'] = panel.alpha
			panel_telem['beta'] = panel.beta
			panel_telem['f'] = panel.f
			panel_telem['one_lower'] = panel.one_lower
			panel_telem['r_qc_fC'] = panel.r_qc_fC.tolist()
			panel_telem['L'] = panel.L
			panel_telem['D'] = panel.D
			panel_telem['F'] = panel.F.tolist()
			panel_telem['M'] = panel.M.tolist()
			panel_telem['Cbw'] = panel.Cbw.flatten().tolist()
		
		hull = self.model.hull
		hull_telem = self.__telem['hull']
		hull_telem['alpha'] = hull.alpha
		hull_telem['beta'] = hull.beta
		hull_telem['area'] = hull.area
		hull_telem['vol'] = hull.vol
		hull_telem['area_center'] = hull.area_center.tolist()
		hull_telem['vol_center'] = hull.vol_center.tolist()
		hull_telem['L'] = hull.L_h
		hull_telem['D'] = hull.D_h
		hull_telem['F_h'] = hull.F_h.tolist()
		hull_telem['M_h'] = hull.M_h.tolist()
		hull_telem['F_b'] = hull.F_b.tolist()
		hull_telem['M_b'] = hull.M_b.tolist()
		hull_telem['Cbw'] = hull.Cbw.flatten().tolist()

		surf_telem = hull_telem['surf']
		surf_telem['alpha'] = hull.alpha_surf
		surf_telem['beta'] = hull.beta_surf
		surf_telem['L'] = hull.L_surf
		surf_telem['D'] = hull.D_surf
		surf_telem['F'] = hull.F_surf.tolist()
		surf_telem['M'] = hull.M_surf.tolist()
		surf_telem['Cbw'] = hull.Cbw_surf.flatten().tolist()

		for wr in self.model.wing_roots:
			wr_telem = self.__telem['wing_roots'][str(int(not wr.left))]
			wr_telem['alpha'] = wr.alpha
			wr_telem['beta'] = wr.beta
			wr_telem['area'] = wr.area
			wr_telem['vol'] = wr.vol
			wr_telem['area_center'] = wr.area_center.tolist()
			wr_telem['vol_center'] = wr.vol_center.tolist()
			wr_telem['L'] = wr.L
			wr_telem['D'] = wr.D
			wr_telem['F_f'] = wr.F_f.tolist()
			wr_telem['M_f'] = wr.M_f.tolist()
			wr_telem['F_b'] = wr.F_b.tolist()
			wr_telem['M_b'] = wr.M_b.tolist()
			wr_telem['Cbw'] = wr.Cbw.flatten().tolist()
		
		p = self.model.propulsor
		p_telem = self.__telem['propulsor']
		p_telem['beta'] = p.beta
		p_telem['fp'] = p.fp
		p_telem['I'] = p.I
		p_telem['omega'] = p.omega
		p_telem['epsilon'] = p.epsilon
		p_telem['T'] = p.T
		p_telem['Q'] = p.Q
		p_telem['F'] = p.F.tolist()
		p_telem['M'] = p.M.tolist()
		p_telem['Cra_w'] = p.Cra_w.flatten().tolist()
		
		self.__telem['U'] = self.model.U.tolist()
		self.__telem['omega'] = self.model.omega.tolist()
		self.__telem['Phi'] = self.model.Phi.tolist()
		self.__telem['r'] = self.model.r.tolist()
		self.__telem['psi_ra'] = self.model.psi_ra
		self.__telem['C0b'] = self.model.C0b.flatten().tolist()
		self.__telem['Cb_ra'] = self.model.Cb_ra.flatten().tolist()

		self.__telem['running'] = self.__running
		self.telem = json.dumps(self.__telem)

sim = Simulation(model_RB.make_default())
sockets = set()

# --- Joystick Link ---
pygame.init()
pygame.joystick.init()
controller = None

if pygame.joystick.get_count() == 0:
	print(f'INFO: no controller detected')
else:
	try:
		controller = pygame.joystick.Joystick(0)
		controller.init()
		if not controller.get_init():
			print(f'ERROR: controller initialization failed')
		else:	
			print(f'INFO: controller linked - "{controller.get_name()}"')
	except Exception as e:
		print(f'ERROR: controller link failed - {e}')

# --- Network Handlers ---
async def handler(socket: websockets.ServerConnection):
	sockets.add(socket)
	print(f'INFO: connected to {socket.remote_address}')
	await socket.send(sim.build_telem)
	await socket.send(sim.telem)
	try:
		async for message in socket:
			data = json.loads(message)
			try:
				dataType = data['type']
				if dataType == 'set':
					state, value = data['state'], data['value']
					if state == 'U': sim.model.U = np.array([value['x'],value['y'],value['z']])
					elif state == 'omega': sim.model.omega = np.array([value['x'],value['y'],value['z']])*np.pi/180
					elif state == 'Phi': sim.model.Phi = np.array([value['x'],value['y'],value['z']])*np.pi/180
					elif state == 'r': sim.model.r = np.array([value['x'],value['y'],value['z']/100])
					elif state == 'epsilon': sim.model.propulsor.epsilon = value
					elif state == 'psi_ra': sim.model.psi_ra = value*np.pi/180
					else: print(f'WARNING: unknown state set request - {state} = {value}')

					sim.system.set_initial_value(sim.model.get_state(), sim.system.t)
					sim.model.calc_state_dot()
					sim.set_telemetry()
					for socket in sockets:
						await socket.send(sim.telem)
				elif dataType == 'sim':
					if sim.is_running():
						sim.pause()
						print(f'INFO: pausing simulation')
					else:
						sim.resume()
						print(f'INFO: resuming simulation')
				elif dataType == 'step':
					print(f'INFO: stepping simulation by {data['dt']} second(s)')
					sim.step(data['dt'])

					sim.model.calc_state_dot()
					sim.set_telemetry()
					for socket in sockets:
						await socket.send(sim.telem)
				elif dataType == 'reset':
					print(f'INFO: resetting simulation')
					sim.reset()
					
					for socket in sockets:
						await socket.send(sim.telem)
				else:
					print(f'WARNING: unknown data received - {data}')
			except Exception as e:
				print(f'ERROR: corrupt data received "{data}" - {e}')
	except websockets.ConnectionClosed:
		pass
	finally:
		sockets.remove(socket)
		print(f'INFO: lost connection to {socket.remote_address}')
		if not sockets and sim.is_running():
			sim.pause()
			print(f'INFO: no remaining sockets, pausing simulation')

# --- Background Loops ---
async def simulation_loop():
	loop_rate = 100
	step_rate = 10
	try:
		while True:
			# step and transmit telemetry
			if sim.is_running() and sim.get_dt() > 1/step_rate:
				sim.step()
				
				sim.model.calc_state_dot()
				sim.set_telemetry()
				for socket in sockets:
					await socket.send(sim.telem)
			await asyncio.sleep(1/loop_rate)
	except asyncio.CancelledError:
		print('INFO: simulation terminated')
	except Exception as e:
		print(f'ERROR: simulation error - {e}')

async def console_input():
	sentinel = ['q', 'quit', 'stop', 'exit']
	while True:
		cmd = await asyncio.to_thread(input)
		if cmd.lower() in sentinel:
			print('INFO: termination received')
			break
		print(f"INFO: received: {cmd}")

async def controller_input():
	if controller is None: return
	try:
		while True:
			pygame.event.pump()

			yaw = controller.get_axis(0)
			throttle = controller.get_axis(1)
	except asyncio.CancelledError: pass

# --- Entry Point ---
async def main():
	port = 8765
	async with websockets.serve(handler, 'localhost', port):
		print(f'INFO: simulation server started on port {port}')

		sim_task = asyncio.create_task(simulation_loop())
		controller_task = asyncio.create_task(controller_input())

		try:
			await console_input()
		except asyncio.CancelledError:
			print(f'\fINFO: terminating')
		finally:
			sim_task.cancel()
			await controller_task
			results = await asyncio.gather(sim_task, return_exceptions=True)
			results = list(filter(None, results))
			if results:
				print(f'INFO: termination completed with {len(results)} error(s) - {results}')
			else:
				print(f'INFO: termination complete')

if __name__ == '__main__': asyncio.run(main())