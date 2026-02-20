import { Pane } from 'tweakpane';

export class UI {
	constructor(callbacks = {}) {
		this.leftPane = new Pane({
			container: document.getElementById('pane-left')
		});

		this.rightPane = new Pane({
			container: document.getElementById('pane-right')
		});

		this.callbacks = callbacks;
		this.socketParams = {
			url: 'ws://localhost:9000',
			status: 'Disconnected'
		};
		this.sceneConfig = {
			cameraFollow: true,
			cameraTarget: false,
			stlOpacity: 0.8,
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
		};
		this.simStates = {
			U: {u: 0, v: 0, w: 0},
			omega: {p: 0, q: 0, r: 0},
			Phi: {phi: 0, theta: 0, psi: 0},
			r: {x: 0, y: 0, z: 0},
			I: 0,
			RPM: 0,
			V: 0,
			psi_ra: 0,
			rate: 1
		}
		this.controlStates = {
			U: {x: 0, y: 0, z: 0},
			omega: {x: 0, y: 0, z: 0},
			Phi: {x: 0, y: 0, z: 0},
			r: {x: 0, y: 0, z: 0},
			input: {x: 0, y: 0},
			rate: 1,
			log_dt: -2
		}
		this.telem = {
			raw: 'N/A'
		}
		this.telemFunc = function(k,v) {
			if (Object.prototype.toString.call(v) === '[object Array]') {
				// return JSON.stringify(b, this.telemFunc, 2)
				if (k.startsWith('C')) {
					v = v.map(val => parseFloat(val).toFixed(4));
					let lst = [
						v.slice(0,3),
						v.slice(3,6),
						v.slice(6,9),
					]
					return lst
				}
				else {
					return '<'+v.map(val => parseFloat(val).toFixed(4)).join(', ')+'>'
				}
			} else if (Object.prototype.toString.call(v) === '[object Number]') {
				return parseFloat(v).toFixed(4);
			}
			return v
		}
		this.#init();
	}
	#init() {
		// --- Left Pane ---
		const socketFolder = this.leftPane.addFolder({ title: 'WebSocket' });
		socketFolder.addBinding(this.socketParams, 'url');
		socketFolder.addBinding(this.socketParams, 'status', { readonly: true });
		this.connectBtn = socketFolder.addButton({ title: 'Connect' });
		this.connectBtn.on('click', () => { this.callbacks.onConnect(this.socketParams.url) })
		// -- Telemetry --
		const telemFolder = this.leftPane.addFolder({ title: 'Telemetry' });
		telemFolder.addButton({ title: 'Build' }).on('click', () => console.log(this.telem.build));
		telemFolder.addButton({ title: 'Raw' }).on('click', () => console.log(this.telem.raw));
		telemFolder.addButton({ title: 'Hull' }).on('click', () => console.log(this.telem.hull));
		telemFolder.addButton({ title: 'Wings' }).on('click', () => console.log(this.telem.panels));
		telemFolder.addButton({ title: 'Wing Roots' }).on('click', () => console.log(this.telem.wing_roots));
		telemFolder.addButton({ title: 'Propulsor' }).on('click', () => console.log(this.telem.propulsor));
		telemFolder.addButton({ title: 'Misc' }).on('click', () => console.log(this.telem.misc));
		// -- Camera --
		const camFolder = this.leftPane.addFolder({ title: 'Camera' });
		camFolder.addButton({ title: 'Refocus Camera' }).on('click', () => this.callbacks.onRefocusCamera());
		camFolder.addBinding(this.sceneConfig, 'cameraFollow', { label: 'Camera Follow' })
			.on('change', () => this.targetBinding.disabled = this.sceneConfig.cameraFollow);
		this.targetBinding = camFolder.addBinding(this.sceneConfig, 'cameraTarget', { label: 'Camera Target', 
			disabled: this.sceneConfig.cameraFollow });
		// -- Simulation --
		const simFolder = this.leftPane.addFolder({ title: 'Simulation' });
		simFolder.addBinding(this.simStates, 'rate', { readonly: true });
		simFolder.addBinding(this.controlStates, 'rate', { label: 'target rate', min: 0.1, max: 1 }).on('change', ev => this.callbacks.onStateChange('speed', ev.value))
		this.methodList = simFolder.addBlade({
			view: 'list',
			label: 'method',
			options: [
				{ text: 'RK45', value: 'RK45' },
				{ text: 'RK23', value: 'RK23' },
				{ text: 'Radau', value: 'Radau' },
				{ text: 'BDF', value: 'BDF' },
			],
			value: 'RK45'
		}).on('change', ev => this.callbacks.onStateChange('method', ev.value));
		this.runBtn = simFolder.addButton({ title: 'Run' }).on('click', () => {
			this.runBtn.disabled = true;
			this.stepBtn.disabled = true;
			this.#disableControls(true);
			this.callbacks.onToggleRun();
		});
		simFolder.addBinding(this.controlStates, 'log_dt', { label: 'log(Δt)', min: -3, max: -1 });
		this.stepBtn = simFolder.addButton({ title: 'Step' }).on('click', () => this.callbacks.onStep());
		this.reinitBtn = simFolder.addButton({ title: 'Re-initialize' }).on('click', () => this.callbacks.onReinit());
		// -- Scene --
		const sceneFolder = this.leftPane.addFolder({ title: 'Scene' });
		sceneFolder.addButton({ title: 'Light Helpers' }).on('click', () => this.callbacks.onToggleLightHelpers());
		// -- STL --
		const stlFolder = sceneFolder.addFolder({ title: 'STL' });
		stlFolder.addButton({ title: 'Hull' }).on('click', () => this.callbacks.onToggleHull());
		stlFolder.addButton({ title: 'Wings' }).on('click', () => this.callbacks.onToggleWings());
		stlFolder.addButton({ title: 'Rear Wings' }).on('click', () => this.callbacks.onToggleRearWings());
		stlFolder.addBinding(this.sceneConfig, 'stlOpacity', { label: 'Opacity', min: 0, max: 1 }).on('change', () => this.callbacks.onStlOpacity());
		// -- Waterplane --
		const waterplaneFolder = sceneFolder.addFolder({ title: 'Waterplane' });
		waterplaneFolder.addBinding(this.sceneConfig, 'waterplaneColor', { label: 'Waterplane' }).on('change', () => this.callbacks.onVisuals());
		waterplaneFolder.addBinding(this.sceneConfig, 'waterplaneOpacity', { label: 'Opacity', min: 0, max: 1 }).on('change', () => this.callbacks.onVisuals());
		waterplaneFolder.addButton({ title: 'Waterplane' }).on('click', () => this.callbacks.onToggleWaterplane());
		waterplaneFolder.addButton({ title: 'Grid' }).on('click', () => this.callbacks.onToggleGrid());

		// --- Right Pane ---
		const rightTabs = this.rightPane.addTab({
			pages: [
				{title: 'Visuals'},
				{title: 'States'}
			]
		})

		// --- Scene Tab ---
		// -- Panels --
		const panelsFolder = rightTabs.pages[0].addFolder({ title: 'Panels' });
		panelsFolder.addBinding(this.sceneConfig, 'surfColor', { label: 'Surfaced' }).on('change', () => this.callbacks.onVisuals());
		panelsFolder.addBinding(this.sceneConfig, 'subColor', { label: 'Submerged' }).on('change', () => this.callbacks.onVisuals());
		panelsFolder.addBinding(this.sceneConfig, 'submergenceScale', { label: 'Submergence', min: 0, max: 0.5 }).on('change', () => this.callbacks.onVisuals());
		panelsFolder.addButton({ title: 'Surfaced' }).on('click', () => this.callbacks.onToggleSurfaced());
		panelsFolder.addButton({ title: 'Submerged' }).on('click', () => this.callbacks.onToggleSubmerged());
		panelsFolder.addButton({ title: 'Submergence' }).on('click', () => this.callbacks.onToggleSubmergence());
		// -- Vectors --
		const vectorFolder = rightTabs.pages[0].addFolder({ title: 'Vectors' })
		vectorFolder.addBinding(this.sceneConfig, 'forceColor', { label: 'Forces' }).on('change', () => this.callbacks.onVisuals());
		vectorFolder.addBinding(this.sceneConfig, 'momentColor', { label: 'Moments' }).on('change', () => this.callbacks.onVisuals());
		vectorFolder.addBinding(this.sceneConfig, 'forceScale', { label: 'Force Scale', min: 0, max: 0.001 }).on('change', () => this.callbacks.onVisuals());
		vectorFolder.addBinding(this.sceneConfig, 'momentScale', { label: 'Moment Scale', min: 0, max: 0.01 }).on('change', () => this.callbacks.onVisuals());
		vectorFolder.addButton({ title: 'Force Vectors' }).on('click', () => this.callbacks.onToggleForces());
		vectorFolder.addButton({ title: 'Moment Vectors' }).on('click', () => this.callbacks.onToggleMoments());
		// -- Axes --
		const axesFolder = rightTabs.pages[0].addFolder({ title: 'Axes' });
		axesFolder.addBinding(this.sceneConfig, 'hullAxesScale', { label: 'Hull Scale', min: 0, max: 1 }).on('change', () => this.callbacks.onVisuals());
		axesFolder.addBinding(this.sceneConfig, 'foilAxesScale', { label: 'Foil Scale', min: 0, max: 0.5 }).on('change', () => this.callbacks.onVisuals());
		axesFolder.addBinding(this.sceneConfig, 'propAxesScale', { label: 'Propulsor Scale', min: 0, max: 0.5 }).on('change', () => this.callbacks.onVisuals());
		axesFolder.addButton({ title: 'Hull Axes' }).on('click', () => this.callbacks.onToggleHullAxes());
		axesFolder.addButton({ title: 'Foil Axes' }).on('click', () => this.callbacks.onToggleFoilAxes());
		axesFolder.addButton({ title: 'Propulsor Axes' }).on('click', () => this.callbacks.onTogglePropulsorAxes());
		// -- Frames --
		const frameFolder = rightTabs.pages[0].addFolder({ title: 'Coordinate Frames' });
		frameFolder.addButton({ title: 'Fixed Frame' }).on('click', () => this.callbacks.onToggleFixedFrame());
		frameFolder.addButton({ title: 'Body Frame' }).on('click', () => this.callbacks.onToggleBodyFrame());
		frameFolder.addButton({ title: 'Rear Axle Frame' }).on('click', () => this.callbacks.onToggleRearAxleFrame());

		// --- States Tab ---
		this.syncBtn = rightTabs.pages[1].addButton({ title: 'Sync States' }).on('click', () => {
			this.syncControlStates();
			this.syncInputs(this.constants);
		})
		this.resetBtn = rightTabs.pages[1].addButton({ title: 'Zero States' }).on('click', () => this.callbacks.onReset());
		// -- U --
		const UFolder = rightTabs.pages[1].addFolder({ title: 'Velocities' });
		UFolder.addBinding(this.simStates.U, 'u', { label: 'u [m/s]', readonly: true });
		UFolder.addBinding(this.simStates.U, 'v', { label: 'v [m/s]', readonly: true });
		UFolder.addBinding(this.simStates.U, 'w', { label: 'w [m/s]', readonly: true });
		this.UControl = UFolder.addBinding(this.controlStates, 'U', {
			label: '<u,v,w>',
			x: { min: -5, max: 20 },
			y: { min: -1, max: 1 },
			z: { min: -1, max: 1 },
		}).on('change', ev => this.callbacks.onStateChange('U', ev.value));
		// -- omega --
		const omegaFolder = rightTabs.pages[1].addFolder({ title: 'Angular Rates' });
		omegaFolder.addBinding(this.simStates.omega, 'p', { label: 'p [°/s]', readonly: true });
		omegaFolder.addBinding(this.simStates.omega, 'q', { label: 'q [°/s]', readonly: true });
		omegaFolder.addBinding(this.simStates.omega, 'r', { label: 'r [°/s]', readonly: true });
		this.omegaControl = omegaFolder.addBinding(this.controlStates, 'omega', { 
			label: '<p,q,r>',
			x: { min: -60, max: 60 },
			y: { min: -60, max: 60 },
			z: { min: -60, max: 60 },
		}).on('change', ev => this.callbacks.onStateChange('omega', ev.value));
		// -- Phi --
		const PhiFolder = rightTabs.pages[1].addFolder({ title: 'Euler Angles' });
		PhiFolder.addBinding(this.simStates.Phi, 'phi', { label: 'ϕ [°]', readonly: true });
		PhiFolder.addBinding(this.simStates.Phi, 'theta', { label: 'θ [°]', readonly: true });
		PhiFolder.addBinding(this.simStates.Phi, 'psi', { label: 'ψ [°]', readonly: true });
		this.PhiControl = PhiFolder.addBinding(this.controlStates, 'Phi', {
			label: '<ϕ,θ,ψ>',
			x: { min: -60, max: 60 },
			y: { min: -45, max: 45 },
			z: { min: 0, max: 360 }
		}).on('change', ev => this.callbacks.onStateChange('Phi', ev.value));
		// -- r --
		const rFolder = rightTabs.pages[1].addFolder({ title: 'Position' });
		rFolder.addBinding(this.simStates.r, 'x', { label: 'x [m]', readonly: true });
		rFolder.addBinding(this.simStates.r, 'y', { label: 'y [m]', readonly: true });
		rFolder.addBinding(this.simStates.r, 'z', { label: 'z [cm]', readonly: true });
		this.rControl = rFolder.addBinding(this.controlStates, 'r', {
			label: '<x,y,z>',
			z: { min: -50, max: 50 }
		}).on('change', ev => this.callbacks.onStateChange('r', ev.value));
		// -- Propulsor --
		const propFolder = rightTabs.pages[1].addFolder({ title: 'Propulsor States' });
		propFolder.addButton({ title: 'Zero Inputs' }).on('click', () => {
			this.controlStates.input.x = 0;
			this.controlStates.input.y = 0;
			this.rightPane.refresh();
		})
		propFolder.addBinding(this.simStates, 'RPM', { label: 'RPM', readonly: true });
		propFolder.addBinding(this.simStates, 'I', { label: 'I [A]', readonly: true });
		propFolder.addBinding(this.simStates, 'psi_ra', { label: 'ψ-ra [°]', readonly: true });
		propFolder.addBinding(this.simStates, 'V', { label: 'V [V]', readonly: true });
		propFolder.addBinding(this.controlStates, 'input', { 
			label: '<%ψ,%V>', 
			picker: 'inline',
			expanded: true,
			x: { min: -1, max: 1 },
			y: { min: -1, max: 1, inverted: true }
		}).on('change', ev => this.callbacks.onStateChange('input', ev.value));
	}
	updateSocketStatus(status) {
		this.socketParams.status = status;
		this.connectBtn.disabled = status != 'Disconnected';
	}
	updateSimulationStatus(running) {
		if (this.simStates.running && !running) this.callbacks.onPause();
		this.simStates.running = running
		this.runBtn.title = running? 'Pause': 'Resume';
		this.runBtn.disabled = false;
		this.#disableControls(running);
	}
	#disableControls(disabled) {
		this.stepBtn.disabled = disabled;
		this.UControl.disabled = disabled;
		this.omegaControl.disabled = disabled;
		this.PhiControl.disabled = disabled;
		this.rControl.disabled = disabled;
		this.methodList.disabled = disabled;
	}
	setTelem(msg) {
		this.telem.raw = msg;
		this.telem.json = JSON.stringify(msg, this.telemFunc, 2);
		this.telem.hull = JSON.stringify(msg['hull'], this.telemFunc, 2);
		this.telem.panels = JSON.stringify(msg['panels'], this.telemFunc, 2);
		this.telem.wing_roots = JSON.stringify(msg['wing_roots'], this.telemFunc, 2);
		this.telem.propulsor = JSON.stringify(msg['propulsor'], this.telemFunc, 2);
		const { hull, panels, wing_roots, propulsor, type, ...otherProperties } = msg;
		this.telem.misc = JSON.stringify(otherProperties, this.telemFunc, 2);
	}
	setMethod(method) {
		this.methodList.value = method;
	}
	setBuildTelem(msg) {
		this.telem.build = JSON.stringify(msg, this.telemFunc, 2);
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

		this.rightPane.refresh();
	}
	syncInputs() {
		this.controlStates.input.x = -this.simStates.psi_ra / this.constants.psi_ra_max;
		this.controlStates.input.y = this.simStates.V / this.constants.V_max;

		this.rightPane.refresh();
	}
}