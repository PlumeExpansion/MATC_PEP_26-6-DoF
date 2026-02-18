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
			url: 'ws://localhost:8765',
			status: 'Disconnected'
		};
		this.sceneConfig = {
			stlOpacity: 0.7,
			hullAxesScale: 0.5,
			foilAxesScale: 0.25,
			propAxesScale: 0.25,
			forceScale: 0.001,
			momentScale: 0.01,
			submergenceScale: 0.5,
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
			epsilon: 0,
			psi_ra: 0,
			status: 'Paused'
		}
		this.controlStates = {
			U: {x: 0, y: 0, z: 0},
			omega: {x: 0, y: 0, z: 0},
			Phi: {x: 0, y: 0, z: 0},
			r: {x: 0, y: 0, z: 0},
			epsilon: 0,
			psi_ra: 0,
			dt: 0.1
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
		// --- WebSocket Tab ---
		const socketFolder = this.leftPane.addFolder({ title: 'WebSocket' });
		socketFolder.addBinding(this.socketParams, 'url');
		socketFolder.addBinding(this.socketParams, 'status', { readonly: true });
		this.connectBtn = socketFolder.addButton({ title: 'Connect' });
		this.connectBtn.on('click', () => {
			this.callbacks.onConnect(this.socketParams.url);
		})

		const telemFolder = this.leftPane.addFolder({ title: 'Telemetry' });
		telemFolder.addButton({ title: 'Raw' }).on('click', () => console.log(this.telem.raw));
		telemFolder.addButton({ title: 'Hull' }).on('click', () => console.log(this.telem.hull));
		telemFolder.addButton({ title: 'Wings' }).on('click', () => console.log(this.telem.panels));
		telemFolder.addButton({ title: 'Wing Roots' }).on('click', () => console.log(this.telem.wing_roots));
		telemFolder.addButton({ title: 'Propulsor' }).on('click', () => console.log(this.telem.propulsor));
		telemFolder.addButton({ title: 'Misc' }).on('click', () => console.log(this.telem.misc));

		const rightTabs = this.rightPane.addTab({
			pages: [
				{title: 'Scene'},
				{title: 'Simulation'}
			]
		})

		// --- Scene Tab ---
		rightTabs.pages[0].addButton({
			title: 'Light Helpers',
		}).on('click', () => this.callbacks.onToggleLightHelpers());
		rightTabs.pages[0].addButton({
			title: 'Refocus Camera',
		}).on('click', () => this.callbacks.onRefocusCamera());
		
		const stlFolder = rightTabs.pages[0].addFolder({ title: 'STL Models' });
		stlFolder.addButton({ title: 'Hull' }).on('click', () => this.callbacks.onToggleHull());
		stlFolder.addButton({ title: 'Wings' }).on('click', () => this.callbacks.onToggleWings());
		stlFolder.addButton({ title: 'Rear Wings' }).on('click', () => this.callbacks.onToggleRearWings());
		stlFolder.addBinding(this.sceneConfig, 'stlOpacity', { label: 'Opacity', min: 0, max: 1 }).on('change', () => this.callbacks.onStlOpacity());

		const panelsFolder = rightTabs.pages[0].addFolder({ title: 'Panels' });
		panelsFolder.addBinding(this.sceneConfig, 'surfColor', { label: 'Surfaced' }).on('change', () => this.callbacks.onVisuals());
		panelsFolder.addBinding(this.sceneConfig, 'subColor', { label: 'Submerged' }).on('change', () => this.callbacks.onVisuals());
		panelsFolder.addBinding(this.sceneConfig, 'submergenceScale', { label: 'Submergence', min: 0, max: 1 }).on('change', () => this.callbacks.onVisuals());
		panelsFolder.addButton({ title: 'Surfaced' }).on('click', () => this.callbacks.onToggleSurfaced());
		panelsFolder.addButton({ title: 'Submerged' }).on('click', () => this.callbacks.onToggleSubmerged());
		panelsFolder.addButton({ title: 'Submergence' }).on('click', () => this.callbacks.onToggleSubmergence());
		
		const vectorFolder = rightTabs.pages[0].addFolder({ title: 'Vectors' })
		vectorFolder.addBinding(this.sceneConfig, 'forceColor', { label: 'Forces' }).on('change', () => this.callbacks.onVisuals());
		vectorFolder.addBinding(this.sceneConfig, 'momentColor', { label: 'Moments' }).on('change', () => this.callbacks.onVisuals());
		vectorFolder.addBinding(this.sceneConfig, 'forceScale', { label: 'Force Scale', min: 0, max: 0.001 }).on('change', () => this.callbacks.onVisuals());
		vectorFolder.addBinding(this.sceneConfig, 'momentScale', { label: 'Moment Scale', min: 0, max: 0.01 }).on('change', () => this.callbacks.onVisuals());
		vectorFolder.addButton({ title: 'Force Vectors' }).on('click', () => this.callbacks.onToggleForces());
		vectorFolder.addButton({ title: 'Moment Vectors' }).on('click', () => this.callbacks.onToggleMoments());
		
		const axesFolder = rightTabs.pages[0].addFolder({ title: 'Axes' });
		axesFolder.addBinding(this.sceneConfig, 'hullAxesScale', { label: 'Hull Scale', min: 0, max: 1 }).on('change', () => this.callbacks.onVisuals());
		axesFolder.addBinding(this.sceneConfig, 'foilAxesScale', { label: 'Foil Scale', min: 0, max: 0.5 }).on('change', () => this.callbacks.onVisuals());
		axesFolder.addBinding(this.sceneConfig, 'propAxesScale', { label: 'Propulsor Scale', min: 0, max: 0.5 }).on('change', () => this.callbacks.onVisuals());
		axesFolder.addButton({ title: 'Hull Axes' }).on('click', () => this.callbacks.onToggleHullAxes());
		axesFolder.addButton({ title: 'Foil Axes' }).on('click', () => this.callbacks.onToggleFoilAxes());
		axesFolder.addButton({ title: 'Propulsor Axes' }).on('click', () => this.callbacks.onTogglePropulsorAxes());

		// --- Simulation Tab ---
		rightTabs.pages[1].addBinding(this.simStates, 'status', { readonly: true });
		this.runBtn = rightTabs.pages[1].addButton({ title: 'Run' }).on('click', () => {
			this.runBtn.disabled = true;
			this.stepBtn.disabled = true;
			this.#disableControls(true);
			this.callbacks.onToggleRun();
		});
		this.stepBtn = rightTabs.pages[1].addButton({ title: 'Step' }).on('click', () => this.callbacks.onStep())
		this.resetBtn = rightTabs.pages[1].addButton({ title: 'Reset' }).on('click', () => this.callbacks.onReset())
		rightTabs.pages[1].addBinding(this.controlStates, 'dt', { label: 'Δt', min: 0.01, max: 1 });
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
		
		const PhiFolder = rightTabs.pages[1].addFolder({ title: 'Euler Angles' });
		PhiFolder.addBinding(this.simStates.Phi, 'phi', { label: 'ϕ [°]', readonly: true });
		PhiFolder.addBinding(this.simStates.Phi, 'theta', { label: 'θ [°]', readonly: true });
		PhiFolder.addBinding(this.simStates.Phi, 'psi', { label: 'ψ [°]', readonly: true });
		this.PhiControl = PhiFolder.addBinding(this.controlStates, 'Phi', {
			label: '<ϕ,θ,ψ>',
			x: { min: -60, max: 60 },
			y: { min: -45, max: 45 },
			z: { min: -180, max: 180 }
		}).on('change', ev => this.callbacks.onStateChange('Phi', ev.value));
		
		const rFolder = rightTabs.pages[1].addFolder({ title: 'Position' });
		rFolder.addBinding(this.simStates.r, 'x', { label: 'x [m]', readonly: true });
		rFolder.addBinding(this.simStates.r, 'y', { label: 'y [m]', readonly: true });
		rFolder.addBinding(this.simStates.r, 'z', { label: 'z [cm]', readonly: true });
		this.rControl = rFolder.addBinding(this.controlStates, 'r', {
			label: '<x,y,z>',
			z: { min: -50, max: 50 }
		}).on('change', ev => this.callbacks.onStateChange('r', ev.value));
		
		const propFolder = rightTabs.pages[1].addFolder({ title: 'Propulsor States' });
		propFolder.addBinding(this.simStates, 'I', { label: 'I [A]', readonly: true });
		propFolder.addBinding(this.simStates, 'RPM', { label: 'RPM', readonly: true });
		propFolder.addBinding(this.simStates, 'epsilon', { label: 'ε [V]', readonly: true });
		propFolder.addBinding(this.simStates, 'psi_ra', { label: 'ψ-ra [°]', readonly: true });
		propFolder.addBinding(this.controlStates, 'epsilon', { label: 'ε [V]', min: -44.4, max: 44.4 })
			.on('change', ev => this.callbacks.onStateChange('epsilon', ev.value));
		propFolder.addBinding(this.controlStates, 'psi_ra', { label: 'ψ-ra [°]', min: -15, max: 15 })
			.on('change', ev => this.callbacks.onStateChange('psi_ra', ev.value));
	}
	updateSocketStatus(status) {
		this.socketParams.status = status;
		this.connectBtn.disabled = status != 'Disconnected';
	}
	updateSimulationStatus(running) {
		this.simStates.status = running? 'Running' : 'Paused';
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
		this.leftPane.refresh();
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

		this.controlStates.epsilon = this.simStates.epsilon;
		this.controlStates.psi_ra = this.simStates.psi_ra;

		this.rightPane.refresh();
	}
}