import asyncio
import websockets
import json
import numpy as np

import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
os.environ['PYTHONWARNINGS'] = 'ignore'
import pygame

import model_RBird as model_RB
from simulation import Simulation

# --- Simulation Logic --

sim = Simulation(model_RB.make_default())
sockets = set()

async def broadcast_telem():
	for socket in sockets:
		await socket.send(sim.telem)

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
					elif state == 'speed': sim.base_speed = value
					elif state == 'input':
						psi_ra = -value['x']*np.pi/180
						V = value['y']
						if sim.is_running():
							sim.input_queued = True
							sim.psi_ra = psi_ra
							sim.V = V
						else:
							sim.model.psi_ra = psi_ra
							sim.V = V
					else: print(f'WARNING: unknown state set request - {state} = {value}')
					if not sim.is_running():
						sim.model.calc_state_dot()
						sim.set_telemetry()

						await broadcast_telem()
				elif dataType == 'sim':
					if sim.is_running():
						sim.pause()
						print(f'INFO: pausing simulation')
						sim.set_telemetry()
						
						await broadcast_telem()
					else:
						sim.resume()
						print(f'INFO: resuming simulation')
				elif dataType == 'step':
					print(f'INFO: stepping simulation by {data['dt']} second(s)')
					sim.step(data['dt'])

					sim.model.calc_state_dot()
					sim.set_telemetry()

					await broadcast_telem()
				elif dataType == 'reset':
					print(f'INFO: resetting simulation')
					sim.reset()
					
					await broadcast_telem()
				elif dataType == 'reinit':
					print(f'INFO: re-initializing simulation')
					sim.pause()
					sim.set_model(model_RB.make_default())

					sim.model.calc_state_dot()
					sim.set_telemetry()

					for socket in sockets:
						socket.send(sim.build_telem)
						socket.send(sim.telem)
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
	step_rate = 20
	try:
		while True:
			# step and transmit telemetry
			if sim.is_running() and sim.get_dt() > 1/step_rate:
				sim.step()
				
				sim.model.calc_state_dot()
				sim.set_telemetry()
				
				await broadcast_telem()
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
	port = 9000
	async with websockets.serve(handler, '127.0.0.1', port):
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