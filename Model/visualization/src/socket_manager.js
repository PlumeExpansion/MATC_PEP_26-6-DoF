export class SocketManager {
	constructor(tm, visualizer) {
		this.tm = tm;
		this.visualizer = visualizer;
		this.socket = null;

		this.onMessageReceived = (msg) => {
			if (msg['type'] == 'build') {
				tm.setBuildTelem(msg);
				visualizer.build(msg);
			} else if (msg['type'] == 'telem') {
				tm.setTelem(msg);
				visualizer.telem(msg);
			} else {
				console.log('WARNING: unknown data received', msg)
			}
		},
		this.onStatusChange = (status) => {
			if (status == 'Disconnected') tm.syncFlag = true;
			tm.updateSocketStatus(status)
		}

		tm.callbacks.onConnect = (url) => this.connect(url);
		tm.callbacks.onStateChange = (state, detail) => {
			if (detail.origin == 'internal')
				this.send({ type: 'set', state: state, value: detail.value });
		};
		tm.callbacks.onToggleRun = () => this.send({ type: 'sim' });
		tm.callbacks.onStep = () => {
			visualizer.syncFlag = true;
			this.send({ type: 'step', dt: tm.controlStates.dt });
		};
		tm.callbacks.onExport = () => this.send({ type: 'export' })
		tm.callbacks.onReset = () => {
			visualizer.syncFlag = true;
			this.send({ type: 'reset' });
		};
		tm.callbacks.onReinit = () => {
			visualizer.syncFlag = true;
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