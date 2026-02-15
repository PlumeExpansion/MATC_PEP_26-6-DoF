import { Pane } from 'tweakpane';

export class UI {
	constructor(callbacks) {
		this.pane = new Pane();
		this.callbacks = callbacks;
		this.params = {
			url: 'ws://localhost:8765',
			status: 'Disconnected'
		};
		this.#init();
	}
	#init() {
		const tabs = this.pane.addTab({
			pages: [
				{title: 'Scene'},
				{title: 'WebSocket'},
				{title: 'Simulation'}
			]
		})

		tabs.pages[0].addButton({
			title: 'Light Helpers',
		}).on('click', () => this.callbacks.onToggleLightHelpers())
		const stlFolder = tabs.pages[0].addFolder({ title: 'STL Models' });
		stlFolder.addButton({ title: 'Hull' }).on('click', () => this.callbacks.onToggleHull())
		stlFolder.addButton({ title: 'Wings' }).on('click', () => this.callbacks.onToggleWings())
		stlFolder.addButton({ title: 'Rear Wings' }).on('click', () => this.callbacks.onToggleRearWings())

		tabs.pages[1].addBinding(this.params, 'url');
		tabs.pages[1].addBinding(this.params, 'status', { readonly: true });
		this.connectBtn = tabs.pages[1].addButton({ title: 'Connect' });
		this.connectBtn.on('click', () => {
			this.callbacks.onConnect(this.params.url);
		})
	}
	updateSocketStatus(status) {
		this.params.status = status;
		this.connectBtn.disabled = status != 'Disconnected';
	}
}