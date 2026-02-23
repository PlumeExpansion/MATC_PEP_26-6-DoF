import { mount } from 'svelte';
import App from './src/ui.svelte';

import { Visualizer } from './src/visualizer.js';
import { DataManager } from './src/data_manager.svelte.js';
import { SocketManager } from "./src/socket_manager.js";

const dm = new DataManager();
const visualizer = new Visualizer(dm);
const socket = new SocketManager(dm, visualizer);

socket.connect(dm.socketParams.url);

mount(App, {
	target: document.getElementById('app'),
	props: { dm }
});