import * as THREE from 'three';

export class DataManager {
	socketParams = $state({
		url: 'ws://localhost:9000',
		status: 'Disconnected'
	});
	sceneConfig = $state({
		cameraMode: 'Follow',
		cameraTrack: 'Body',
		stlOpacity: 0.8,
		stlColor: '#ffffff',
		buoyColor: '#f34242',
		buoyScale: 1,
		buoyFlashRate: 0.5,
		buoyTrailCount: 10,
		maxBuoyTrailCount: 20,
		nearBuoyPos: {x: 10, y: -10},
		farBuoyPos: {x: 10, y: -815},
		waterplaneColor: '#75b8ff',
		waterplaneOpacity: 0.3,
		hullAxesScale: 0.5,
		foilAxesScale: 0.25,
		propAxesScale: 0.25,
		forceScale: 0.001,
		momentScale: 0.01,
		submergenceScale: 0.25,
		forceColor: '#007bff',
		momentColor: '#ff00ff',
		surfColor: '#ffffff',
		subColor: '#ff9d00'
	});
	simStates = $state({
		U: {u: 0, v: 0, w: 0},
		omega: {p: 0, q: 0, r: 0},
		Phi: {phi: 0, theta: 0, psi: 0},
		deltaPsi: 0,
		r: {x: 0, y: 0, z: 0},
		I: 0,
		RPM: 0,
		V: 0,
		psi_ra: 0,
		rate: 1,
		method: 'N/A',
		running: false,
		cmdQueued: false,
		time: 0,
		Vmax: 0,
	});
	methods = $state(['N/A']);
	controlStates = $state({
		U: {x: 0, y: 0, z: 0},
		omega: {x: 0, y: 0, z: 0},
		Phi: {x: 0, y: 0, z: 0},
		r: {x: 0, y: 0, z: 0},
		input: {x: 0, y: 0},
		inputDamped: {x: 0, y: 0},
		rate: 1,
		dt: 0.01
	});
	constants = {
		r_CM: new THREE.Vector3(),
		r_ra: new THREE.Vector3(),
		V_tau: 1,
		psi_ra_rate: 5,
		V_max: 44.4,
		psi_ra_max: 15,
		V_params: {
			x0: 1,
			y0: 1
		},
		psi_ra_params: {
			x0: 1,
			y0: 1
		}
	};
	states = {
		r: new THREE.Vector3(),
		C0b: new THREE.Matrix3(),
		Cra_b: new THREE.Matrix3()
	}
	telem = {
		raw: 'N/A',
		wings: {}
	}
	callbacks = {}
	constructor() {
		this.#setMappingParameters();
	}
	#telemFunc(k,v) {
		if (Object.prototype.toString.call(v) === '[object Array]') {
			if (k.startsWith('C')) {
				v = v.map(val => parseFloat(val).toFixed(4));
				let lst = [
					v.slice(0,3),
					v.slice(3,6),
					v.slice(6,9),
				]
				return lst
			}
			else if (v.every(e => typeof e === 'number'))
				return '<'+v.map(val => parseFloat(val).toFixed(4)).join(', ')+'>'
			else return '['+v.join(', ')+']'
		} else if (Object.prototype.toString.call(v) === '[object Number]') {
			return parseFloat(v).toFixed(4);
		}
		return v
	}
	updateSocketStatus(status) {
		this.socketParams.status = status;
	}
	updateSimulationStatus(running) {
		if (this.simStates.running && !running) {
			this.syncControlStates();
			this.syncInputs();
		}
		this.simStates.running = running
		this.simStates.cmdQueued = false;
	}
	setTelem(msg) {
		this.telem.raw = msg;
		this.telem.json = JSON.stringify(msg, this.#telemFunc, 2);
		const { surf, ...hullProperties } = msg['hull']
		this.telem.hull = JSON.stringify(hullProperties, this.#telemFunc, 2);
		this.telem.surf = JSON.stringify(surf, this.#telemFunc, 2);
		const sepPanels = Object.entries(msg['panels']).reduce((acc, [id,value]) => {
			const targetGroup = id.startsWith('r')? 'rear' : 'main';
			acc[targetGroup][id] = value;
			return acc;
		}, { main: {}, rear: {} });
		this.telem.wings.main = JSON.stringify(sepPanels.main, this.#telemFunc, 2);
		this.telem.wings.rear = JSON.stringify(sepPanels.rear, this.#telemFunc, 2);
		this.telem.wings.root = JSON.stringify(msg['wing_roots'], this.#telemFunc, 2);
		this.telem.propulsor = JSON.stringify(msg['propulsor'], this.#telemFunc, 2);
		const { hull, panels, wing_roots, propulsor, type, ...otherProperties } = msg;
		this.telem.misc = JSON.stringify(otherProperties, this.#telemFunc, 2);

		this.simStates.U.u = msg['U'][0];
		this.simStates.U.v = msg['U'][1];
		this.simStates.U.w = msg['U'][2];
		this.simStates.omega.p = msg['omega'][0]*180/Math.PI;
		this.simStates.omega.q = msg['omega'][1]*180/Math.PI;
		this.simStates.omega.r = msg['omega'][2]*180/Math.PI;
		this.simStates.Phi.phi = msg['Phi'][0]*180/Math.PI;
		this.simStates.Phi.theta = msg['Phi'][1]*180/Math.PI;
		const oldPsi = this.simStates.Phi.psi;
		this.simStates.Phi.psi = msg['Phi'][2]*180/Math.PI;
		this.simStates.Phi.psi -= this.simStates.Phi.psi>180? 360 : 0;
		this.simStates.deltaPsi = this.simStates.Phi.psi-oldPsi;
		this.states.r.fromArray(msg['r']);
		this.simStates.r.x = msg['r'][0];
		this.simStates.r.y = msg['r'][1];
		this.simStates.r.z = msg['r'][2]*100;
		this.simStates.psi_ra = msg['psi_ra']*180/Math.PI;
		this.simStates.rate = msg['rate'];
		this.simStates.time = msg['time'];
		this.states.C0b.fromArray(msg['C0b']).transpose();
		this.states.Cra_b.fromArray(msg['Cra_b']).transpose();
		this.states.Cb_ra = this.states.Cra_b.clone().transpose();
	}
	#setMappingParameters() {
		this.constants.V_params.coeffs = this.#getMappingParameters(this.constants.V_params.x0,this.constants.V_params.y0);
		this.constants.psi_ra_params.coeffs = this.#getMappingParameters(this.constants.psi_ra_params.x0,this.constants.psi_ra_params.y0);
	}
	#getMappingParameters(x0,y0) {
		// Piecewise Linear Cubic
		const A = (y0-x0)/(x0*(x0-1)**3);
		const B = 3*(x0-y0)/(x0-1)**3;
		const C = ((y0-3)*x0**3-y0+3*x0*y0)/(x0*(x0-1)**3);
		const D = ((x0-y0)*x0**2)/(x0-1)**3;
		return [A,B,C,D];
	}
	queryMapped(x,params) {
		const xi = Math.abs(x);
		let y = 0;
		if (xi < params.x0) y = params.y0/params.x0*xi;
		else y = params.coeffs[0]*xi**3 + params.coeffs[1]*xi**2 + params.coeffs[2]*xi + params.coeffs[3];
		return Math.sign(x)*y;
	}
	setMethod(method) {
		this.simStates.method = method;
	}
	setBuildTelem(msg) {
		this.telem.build = JSON.stringify(msg, this.#telemFunc, 2);
		
		this.constants.r_CM.fromArray(msg['r_CM']);
		this.constants.r_ra.fromArray(msg['r_ra']);
		this.constants.V_max = msg['V_max'];
		this.constants.psi_ra_max = msg['psi_ra_max']*180/Math.PI;
		this.constants.V_tau = msg['V_tau'];
		this.constants.psi_ra_rate = msg['psi_ra_rate']*180/Math.PI;

		this.constants.V_params.x0 = msg['V_x0'];
		this.constants.V_params.y0 = msg['V_y0'];
		this.constants.psi_ra_params.x0 = msg['psi_ra_x0'];
		this.constants.psi_ra_params.y0 = msg['psi_ra_y0'];
		this.#setMappingParameters();
		
		this.methods = msg['methods'];
	}
	syncControlStates() {
		this.controlStates.U.x = this.simStates.U.u;
		this.controlStates.U.y = this.simStates.U.v;
		this.controlStates.U.z = this.simStates.U.w;
		
		this.controlStates.omega.x = this.simStates.omega.p;
		this.controlStates.omega.y = this.simStates.omega.q;
		this.controlStates.omega.z = this.simStates.omega.r;
		
		this.controlStates.Phi.x = this.simStates.Phi.phi;
		this.controlStates.Phi.y = this.simStates.Phi.theta;
		this.controlStates.Phi.z = this.simStates.Phi.psi;
		
		this.controlStates.r.x = this.simStates.r.x;
		this.controlStates.r.y = this.simStates.r.y;
		this.controlStates.r.z = this.simStates.r.z;
	}
	syncInputs() {
		this.controlStates.input.x = -this.simStates.psi_ra / this.constants.psi_ra_max;
		this.controlStates.input.y = this.simStates.V / this.constants.V_max;
	}
}