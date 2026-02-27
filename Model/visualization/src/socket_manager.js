export class SocketManager {
	constructor(dm, viz) {
		this.dm = dm;
		this.viz = viz;
		this.socket = null;
		
		dm.callbacks.sendInput = () => {
			this.send({ type: 'set', state: 'input', value: dm.controlStates.inputDamped });
		};
		viz.onRender.push((dt) => {
			if (!dm.simStates.running) return;
			dt *= dm.simStates.rate*(dm.simStates.running? 1 : 0);
			const fracV = Math.exp(-dt/dm.constants.V_tau);
			const inputDamped = dm.controlStates.inputDamped;
			const input = dm.controlStates.input;
			const deltaFracPsi_ra = dt*dm.constants.psi_ra_rate/dm.constants.psi_ra_max;
			const offsetPsi_ra = input.x-inputDamped.x;
			const fracPsi_ra = Math.abs(deltaFracPsi_ra/offsetPsi_ra);
			const inputMapped = {
				x: dm.queryMapped(input.x, dm.constants.psi_ra_params),
				y: dm.queryMapped(input.y, dm.constants.V_params)
			};
			inputDamped.x =fracPsi_ra > 1? input.x : offsetPsi_ra*fracPsi_ra + inputDamped.x;
			inputDamped.y = inputDamped.y*fracV + inputMapped.y*(1-fracV);
			dm.callbacks.sendInput();
		});

		this.onMessageReceived = (msg) => {
			if (msg['type'] == 'build') {
				dm.setBuildTelem(msg);
				viz.build(msg);
				viz.buildPropeller();
			} else if (msg['type'] == 'telem') {
				dm.setTelem(msg);
				viz.telem(msg);
			} else {
				console.log('WARNING: unknown data received', msg)
			}
		},
		this.onStatusChange = (status) => {
			if (status == 'Disconnected') dm.syncFlag = true;
			dm.updateSocketStatus(status)
		}

		dm.callbacks.onConnect = (url) => this.connect(url);
		dm.callbacks.onStateChange = (state, detail) => {
			if (detail.origin == 'internal')
				this.send({ type: 'set', state: state, value: detail.value });
		};
		dm.callbacks.onToggleRun = () => this.send({ type: 'sim' });
		dm.callbacks.onStep = () => {
			viz.syncFlag = true;
			this.send({ type: 'step', dt: dm.controlStates.dt });
		};
		dm.callbacks.onExport = () => this.send({ type: 'export' })
		dm.callbacks.onReset = () => {
			viz.syncFlag = true;
			dm.controlStates.inputDamped.x = 0;
			dm.controlStates.inputDamped.y = 0;
			this.send({ type: 'reset' });
		};
		dm.callbacks.onReinit = () => {
			viz.syncFlag = true;
			this.send({ type: 'reinit' });
		}
	}
	connect(url) {
		if (this.socket != null) return;
		this.socket = new WebSocket(url);
		this.onStatusChange('Connecting...');

		this.socket.addEventListener('open', () => {
			console.log('INFO: socket connected');
			this.onStatusChange('Connected');
		});

		this.socket.addEventListener('message', event => {
			let data = undefined;
			try {
				data = JSON.parse(event.data);
			} catch (error) {
				console.error('ERROR: failed to parse data', error, event.data);
				return;
			}
			this.onMessageReceived(data);
		})

		this.socket.addEventListener('close', () => {
			console.log('INFO: socket disconnected');
			this.socket = null;
			this.onStatusChange('Disconnected');
		})

		this.socket.addEventListener('error', err => {
			console.error('ERROR: socket error', err);
			this.socket = null;
			this.onStatusChange('Error');
		})
	}
	send(data) {
		if (this.socket?.readyState === WebSocket.OPEN) {
			this.socket.send(JSON.stringify(data));
		}
	}
}