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
# --- Simulation Handlers ---
async def pause_sim():
	sim.pause()
	print(f'INFO: pausing simulation')
	sim.set_telemetry()
	
	await broadcast_telem()

async def resume_sim():
	sim.resume()
	print(f'INFO: resuming simulation')

async def reset_sim():
	print(f'INFO: resetting simulation')
	sim.reset()
	
	await broadcast_telem()

async def reinit_sim():
	print(f'INFO: re-initializing simulation')
	sim.pause()
	sim.set_model(model_RB.make_default())

	sim.model.calc_state_dot()
	sim.set_telemetry()

	for socket in sockets:
		await socket.send(sim.build_telem)
		await socket.send(sim.telem)

async def step_sim(dt):
	print(f'INFO: stepping simulation by {dt} second(s)')
	sim.step(dt)

	sim.model.calc_state_dot()
	sim.set_telemetry()

	await broadcast_telem()

async def set_method(input_method):
	method = [m for m in sim.valid_methods if m.casefold() == input_method.casefold()]
	if len(method) == 1:
		sim.method = method[0]
		print(f'INFO: setting integration method to {sim.method}')
	else:
		print(f'WARNING: invalid integration method requested - {input_method}')
	
	sim.set_telemetry()
	await broadcast_telem()

async def export_telem():
	try:
		sim.set_formatted_telem()
		path = f'telem/telem_{sim.elapsed:.4f}.txt'
		directory = os.path.dirname(path)
		if not os.path.exists(directory):
			os.makedirs(directory, exist_ok=True)
		with open(path, 'w') as f:
			f.write(sim.formatted_telem)
		print(f'INFO: successfully exported telemetry to "{path}"')
	except Exception as e:
		print(f'ERROR: failed to export telemetry - {e}')

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
					elif state == 'rate': sim.base_rate = value
					elif state == 'method': await set_method(value)
					elif state == 'input':
						psi_ra = -value['x']*sim.model.psi_ra_max
						V = value['y']*sim.model.V_max
						if sim.is_running():
							sim.input_queued = True
							sim.psi_ra = psi_ra
							sim.V = V
						else:
							sim.model.psi_ra = psi_ra
							sim.model.propulsor.V = V
					else: print(f'WARNING: unknown state set request - {state} = {value}')
					if not sim.is_running():
						sim.model.calc_state_dot()
						sim.set_telemetry()

						await broadcast_telem()
				elif dataType == 'sim':
					if sim.is_running(): await pause_sim()
					else: await resume_sim()
				elif dataType == 'step':
					await step_sim(data['dt'])
				elif dataType == 'export':
					await export_telem()
				elif dataType == 'reset':
					await reset_sim()
				elif dataType == 'reinit':
					await reinit_sim()
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
			if sim.get_dt() > 1/step_rate:
				if sim.is_running(): 
					sim.step()

				if sim.is_running() or controller:
					sim.model.calc_state_dot()
					sim.set_telemetry()

					await broadcast_telem()
			await asyncio.sleep(1/loop_rate)
	except asyncio.CancelledError:
		print('INFO: simulation terminated')
	except Exception as e:
		print(f'ERROR: simulation error - {e}')

async def console_loop():
	sentinel = ['q', 'quit', 'stop', 'exit']
	while True:
		cmd = await asyncio.to_thread(input)
		cmd = cmd.lower()
		tokens = cmd.split(' ')
		if cmd in sentinel:
			print('INFO: termination received')
			break
		# console commands
		if cmd == 'pause' or cmd == 'p':
			if sim.is_running():
				await pause_sim()
			else:
				print('INFO: simulation already paused')
		elif cmd == 'resume':
			if sim.is_running():
				print(f'INFO: simulation already running')
			else:
				await resume_sim()
		elif cmd == 'reset':
			await reset_sim()
		elif cmd == 'reinit':
			await reinit_sim()
		elif cmd == 'export':
			await export_telem()
		elif cmd == 'step':
			await step_sim(0.01)
		elif cmd == 'method':
			print(f'INFO: current integration method - {sim.method}')
		elif cmd == 'time':
			print(f'INFO: current elapsed time - {sim.elapsed:.4f}')
		elif len(tokens) == 2:
			cmd = tokens[0]
			arg = tokens[1]
			if cmd == 'step':
				try:
					dt = float(arg)
					if 1e-4 <= dt <= 0.1:
						await step_sim(dt)
					else:
						print(f'ERROR: invalid time step - {arg}')
				except:
					print(f'ERROR: nonfloat time step - {arg}')
			elif cmd == 'method': await set_method(arg)
			else:
				print(f'WARNING: unknown augmented command received - {cmd} - {arg}')
		else:
			print(f'WARNING: unknown command received - {cmd}')

async def controller_loop():
	if controller is None: return
	loop_rate = 100
	try:
		while True:
			pygame.event.pump()

			yaw = controller.get_axis(0)
			throttle = (1-controller.get_axis(2))/2

			reverse = controller.get_button(7)
			
			psi_ra = -yaw*sim.model.psi_ra_max
			V = (-1 if reverse==1 else 1)*throttle*sim.model.V_max
			if sim.is_running():
				sim.input_queued = True
				sim.psi_ra = psi_ra # type: ignore
				sim.V = V # type: ignore
			else:
				sim.model.psi_ra = psi_ra
				sim.model.propulsor.V = V
			await asyncio.sleep(1/loop_rate)
	except asyncio.CancelledError:
		print('INFO: controller link terminated')
	except Exception as e:
		print(f'ERROR: controller error - {e}')

# --- Entry Point ---
async def main():
	port = 9000
	async with websockets.serve(handler, '127.0.0.1', port):
		print(f'INFO: simulation server started on port {port}')

		sim_task = asyncio.create_task(simulation_loop())
		controller_task = asyncio.create_task(controller_loop())

		try:
			await console_loop()
		except asyncio.CancelledError:
			print(f'\fINFO: terminating')
		finally:
			sim_task.cancel()
			controller_task.cancel()
			await controller_task
			results = await asyncio.gather(sim_task, return_exceptions=True)
			results = list(filter(None, results))
			if results:
				print(f'INFO: termination completed with {len(results)} error(s) - {results}')
			else:
				print(f'INFO: termination complete')

if __name__ == '__main__': asyncio.run(main())