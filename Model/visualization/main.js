import { mount } from 'svelte';
import App from './src/ui.svelte';

import { Visualizer } from './src/visualizer.js';
import { TelemetryManager } from './src/telem_manager.svelte.js';
import { SocketManager } from "./src/socket_manager.js";

const tm = new TelemetryManager();
const visualizer = new Visualizer(tm);
const socket = new SocketManager(tm, visualizer);

socket.connect(tm.socketParams.url);
visualizer.renderloop();

mount(App, {
	target: document.getElementById('app'),
	props: { tm }
});