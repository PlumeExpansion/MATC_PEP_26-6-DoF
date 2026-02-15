export class SocketManager {
	constructor(onMessageReceived, onStatusChange) {
		this.socket = null;
		this.onMessageReceived = onMessageReceived;
		this.onStatusChange = onStatusChange;
	}

	connect(url) {
		this.socket = new WebSocket(url);
		this.onStatusChange('Connecting...');

		this.socket.addEventListener('open', () => {
			console.log('INFO: socket connected');
			this.onStatusChange('Connected');
		});

		this.socket.addEventListener('message', event => {
			const data = JSON.parse(event.data);
			this.onMessageReceived(data);
		})

		this.socket.addEventListener('close', () => {
			console.log('INFO: socket disconnected');
			this.onStatusChange('Disconnected');
		})

		this.socket.addEventListener('error', err => {
			console.error('ERROR: socket error', err);
			this.onStatusChange('Error');
		})
	}

	send(data) {
		if (this.socket?.readyState === WebSocket.OPEN) {
			this.socket.send(JSON.stringify(data));
		}
	}
}