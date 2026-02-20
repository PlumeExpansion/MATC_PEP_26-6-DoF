import numpy as np
from scipy.integrate import solve_ivp
import json
import time

from model_RBird import Model_6DoF

class Simulation:
	def __init__(self, model: Model_6DoF):
		self.base_speed = 1
		self.speed = 1
		self.speed_restore = 0.2
		self.speed_boundary = 0.98

		self.time_last = 0
		self.pause()

		self.set_model(model)
		def check_state(t, state):
			criterion = [
				np.abs(state[0]) < 20,
				np.abs(state[1]) < 20,
				np.abs(state[2]) < 20,

				np.abs(state[3]) < 2*np.pi,
				np.abs(state[4]) < 2*np.pi,
				np.abs(state[5]) < 2*np.pi,

				np.abs(state[6]) < 60/180*np.pi,
				np.abs(state[7]) < 45/180*np.pi,
				
				np.abs(state[11]) < 3,
			]
			return all(criterion)
		
		check_state.terminal = True
		self.__check_state = check_state

		self.input_queued = False
		self.V = 0
		self.psi_ra = 0

	def set_model(self, model: Model_6DoF):
		self.model = model
		self.model.calc_state_dot()
		self.__set_build_telem()
		self.__init_telem()
		self.set_telemetry()

	def __get_state_dot(self, t, state):
		self.model.set_state(state)
		self.model.calc_state_dot()
		return self.model.get_state_dot()

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
		self.model.set_input(np.zeros(2))
		self.model.calc_state_dot()
		self.set_telemetry()

	def step(self,dt: float=np.nan):
		if self.input_queued:
			self.input_queued = False
			self.model.propulsor.V = self.V
			self.model.psi_ra = self.psi_ra
		if self.__running:
			if not np.isnan(dt):
				print(f'WARNING: simulation step of {dt} requested while running')
			time_now = time.perf_counter()
			dt = (time_now - self.time_last)
			self.time_last = time_now
		elif np.isnan(dt):
			return
		self.speed = min(self.speed, self.base_speed)
		res = solve_ivp(self.__get_state_dot, [0,dt*self.speed], self.model.get_state(), events=self.__check_state, 
				  method='RK45')
		if self.__running:
			time_now = time.perf_counter()
			solve_dt = time_now-self.time_last
			if solve_dt >= dt:
				self.time_last = time_now
				self.speed = min(dt/solve_dt, self.speed)
				print(f'WARNING: integration time exceeding real time, slowing simulation to {self.speed:.2f} speed')
			elif self.speed < self.speed_boundary * self.base_speed:
				self.speed = self.base_speed*self.speed_restore + self.speed*(1-self.speed_restore)
				if self.speed > self.speed_boundary * self.base_speed:
					self.speed = self.base_speed
				print(f'INFO: restoring simulation speed to {self.speed:.2f}')
		if res.status == -1:
			print(f'WARNING: integration failed, pausing')
			self.pause()
		elif res.status == 0:
			print(f'INFO: {len(res.t)} steps taken')
			self.model.set_state(res.y[:,-1])
		else:
			print(f'WARNING: integration aborted by state check, pausing')
			self.pause()

		return res

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
			},
			'V_max': self.model.V_max,
			'psi_ra_max': self.model.psi_ra_max
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
			panel_telem['U_mag'] = panel.U_mag
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
		hull_telem['U_mag'] = hull.U_mag
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
		surf_telem['U_mag'] = hull.U_mag_surf
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
			wr_telem['U_mag'] = wr.U_mag
			wr_telem['L'] = wr.L
			wr_telem['D'] = wr.D
			wr_telem['F_f'] = wr.F_f.tolist()
			wr_telem['M_f'] = wr.M_f.tolist()
			wr_telem['F_b'] = wr.F_b.tolist()
			wr_telem['M_b'] = wr.M_b.tolist()
			wr_telem['Cbw'] = wr.Cbw.flatten().tolist()
		
		p = self.model.propulsor
		p_telem = self.__telem['propulsor']
		p_telem['fp'] = p.fp
		p_telem['V'] = p.V
		p_telem['n'] = p.n
		p_telem['T'] = p.T
		p_telem['Q'] = p.Q
		p_telem['I'] = p.I
		p_telem['F'] = p.F.tolist()
		p_telem['M'] = p.M.tolist()
		p_telem['Cra_w'] = p.Cra_w.flatten().tolist()
		
		self.__telem['U'] = self.model.U.tolist()
		self.__telem['omega'] = self.model.omega.tolist()
		self.__telem['Phi'] = self.model.Phi.tolist()
		self.__telem['r'] = self.model.r.tolist()
		self.__telem['psi_ra'] = self.model.psi_ra
		self.__telem['C0b'] = self.model.C0b.flatten().tolist()
		self.__telem['Cra_b'] = self.model.Cra_b.flatten().tolist()
		self.__telem['query'] = self.model.query.tolist()

		self.__telem['running'] = self.__running
		self.__telem['speed'] = self.speed
		self.telem = json.dumps(self.__telem)