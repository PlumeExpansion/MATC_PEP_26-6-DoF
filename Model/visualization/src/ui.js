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
		}).on('click', () => {
			this.callbacks.onToggleLightHelpers();
		})

		tabs.pages[1].addBinding(this.params, 'url');
		tabs.pages[1].addBinding(this.params, 'status', { readonly: true });
		tabs.pages[1].addButton({ title: 'Connect' }).on('click', () => {
			this.callbacks.onConnect(this.params.url);
		})
	}
	updateSocketStatus(status) {
		this.params.status = status;
		// this.pane.refresh()
	}
}