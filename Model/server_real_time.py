import asyncio
import websockets
import msgpack
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

	def pause(self):
		self.__running = False

	def resume(self):
		self.__running = True
		self.time_last = time.perf_counter()

	def is_running(self):
		return self.__running

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
async def handler(websocket):
	sockets.add(websocket)
	print(f'INFO: Connection from {websocket.remote_address}')
	try:
		async for message in websocket:
			data = msgpack.unpackb(message)
			# TODO: PROPER COMMAND HANDLING
			# Handle Tweakpane commands here
			# if data.get("type") == "control":
				# sim.running = data["value"]
	except websockets.ConnectionClosed:
		pass
	finally:
		sockets.remove(websocket)
		print(f'INFO: lost connection to {websocket.remote_address}')
		if not sockets:
			sim.pause()
			print(f'INFO: no remaning sockets, pausing simulation')

# --- Background Loops ---
async def simulation_loop():
	loop_rate = 100
	step_rate = 60
	try:
		while True:
			# step and transmit telemetry
			if sim.is_running and sim.get_dt() > 1/step_rate:
				sim.step()

				# TODO: PROPER DATA
				data = {
					"hull": {"F": [10.2, 0, 5], "M": [0, 1.2, 0]},
					"panels": [{"id": 0, "F": [1, 2, 3]}, {"id": 1, "F": [4, 5, 6]}],
					"propulsor": {"thrust": 500.0}
				}
				binary_data = msgpack.packb(data)
				for socket in sockets:
					await socket.send(binary_data)
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
		print(f'INFO: simulation server started on port {8765}')

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