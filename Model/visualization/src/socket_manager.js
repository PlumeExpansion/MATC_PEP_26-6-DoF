export class SocketManager {
	constructor(onMessageReceived, onStatusChange) {
		this.socket = null;
		this.onMessageReceived = onMessageReceived;
		this.onStatusChange = onStatusChange;
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
			try {
				const data = JSON.parse(event.data);
				this.onMessageReceived(data);
			} catch (error) {
				console.error('ERROR: failed to parse data', event.data)
			}
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