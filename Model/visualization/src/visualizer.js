import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { STLLoader } from "three/addons/loaders/STLLoader.js";

import { UI } from "./ui.js";
import { SocketManager } from "./socket_manager.js";
import { Hull } from "./components/hull.js";
import { Panel } from "./components/panel.js";
import { WingRoot } from "./components/wing_root.js";
import { Propulsor } from "./components/propulsor.js";
import * as utils from './utils.js';

// --- Scene Setup ---
const canvas = document.querySelector("canvas.threejs");
const renderer = new THREE.WebGLRenderer({canvas: canvas, antialias: true,});
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))

const scene = new THREE.Scene();

let aspectRatio = window.innerWidth / window.innerHeight;
const camera = new THREE.PerspectiveCamera(35, aspectRatio,0.1,200);

// const aspectRatio = window.innerWidth / window.innerHeight;
// const camera = new THREE.OrthographicCamera(
//   -1 * aspectRatio,
//   1 * aspectRatio,
//   1,
//   -1,
//   0.1,
//   200
// );

camera.position.set(5, -3, -2)
camera.up = new THREE.Vector3(0,0,-1);

const controls = new OrbitControls(camera, canvas);
controls.enableDamping = true;
// controls.autoRotate = true;
controls.zoomSpeed = 2;
controls.zoomToCursor = true;

// --- UI ---
const ui = new UI()

// --- Scene Lighting ---
const ambientLight = new THREE.AmbientLight('white', 0.05);
const topLight = new THREE.DirectionalLight('white', 1.5);
const bottomLight = new THREE.DirectionalLight('white', 0.2);
topLight.position.set(2,-2,-2);
bottomLight.position.set(-2,2,2);
scene.add(ambientLight, topLight, bottomLight);
const topLightHelper = new THREE.DirectionalLightHelper(topLight, 0.5);
const bottomLightHelper = new THREE.DirectionalLightHelper(bottomLight, 0.5);
scene.add(topLightHelper, bottomLightHelper);

ui.callbacks.onToggleLightHelpers = () => {
	topLightHelper.visible = !topLightHelper.visible;
	bottomLightHelper.visible = !bottomLightHelper.visible;
};

// --- Waterplane Grid ---
const grid = new THREE.GridHelper(20, 10);
grid.rotation.x = Math.PI / 2;
scene.add(grid);

// --- STL Models ---
const bodyGroup = new THREE.Group();
const raGroup = new THREE.Group();
bodyGroup.add(raGroup);
scene.add(bodyGroup);

const loader = new STLLoader();
const hullGeometryOrig = await loader.loadAsync('RBird_Hull_Remesh.stl');
const wingGeometryOrig = await loader.loadAsync('Wing_Applied_Low_Poly.stl');
const rearWingGeometryOrig = await loader.loadAsync('Rear_Wing_Applied_Low_Poly.stl');
const material = new THREE.MeshPhongMaterial({color: 'white'});
const hullMesh = new THREE.Mesh(hullGeometryOrig, material);
const wingMesh = new THREE.Mesh(wingGeometryOrig, material);
const rearWingMesh = new THREE.Mesh(rearWingGeometryOrig, material);

bodyGroup.add(hullMesh, wingMesh);
raGroup.add(rearWingMesh);

ui.callbacks.onToggleHull = () => hullMesh.visible = !hullMesh.visible;
ui.callbacks.onToggleWings = () => wingMesh.visible = !wingMesh.visible;
ui.callbacks.onToggleRearWings = () => rearWingMesh.visible = !rearWingMesh.visible;

// --- Components ---
const constants = {
	r_CM: new THREE.Vector3(),
	r_ra: new THREE.Vector3()
};
const states = {
	r: new THREE.Vector3(),
	C0b: new THREE.Matrix3(),
	Cb_ra: new THREE.Matrix3()
}
const panels = new Map();
const wingRoots = new Map([
	['0', new WingRoot(ui.sceneConfig)],
	['1', new WingRoot(ui.sceneConfig)]
]);
const hull = new Hull(ui.sceneConfig);
const propulsor = new Propulsor(ui.sceneConfig);
bodyGroup.add(hull, wingRoots.get('0'), wingRoots.get('1'));
raGroup.add(propulsor);
const components = [hull, propulsor, wingRoots.get('0'), wingRoots.get('1')];

ui.callbacks.onToggleHullAxes = () => hull.toggleAxes();
ui.callbacks.onToggleFoilAxes = () => {
	panels.forEach(panel => panel.toggleAxes());
	wingRoots.values().forEach(wr => wr.toggleAxes());
}
ui.callbacks.onTogglePropulsorAxes = () => propulsor.toggleAxes();
ui.callbacks.onVisuals = () => components.forEach(c => c.syncVisuals());
ui.callbacks.onToggleForces = () => components.forEach(c => c.toggleForces());
ui.callbacks.onToggleMoments = () => components.forEach(c => c.toggleMoments());
ui.callbacks.onToggleSubmerged = () => panels.forEach(p => p.toggleSubmerged());
ui.callbacks.onToggleSurfaced = () => panels.forEach(p => p.toggleSurfaced());
ui.callbacks.onToggleSubmergence = () => panels.forEach(p => p.toggleSubmergence());

function build(msg) {
	constants.r_CM.fromArray(msg['r_CM']);
	constants.r_ra.fromArray(msg['r_ra']);
	raGroup.position.copy(constants.r_ra);
	
	hullMesh.geometry = hullGeometryOrig.clone().translate(-constants['r_CM'].x, -constants['r_CM'].y, -constants['r_CM'].z);
	wingMesh.geometry = wingGeometryOrig.clone().translate(-constants['r_CM'].x, -constants['r_CM'].y, -constants['r_CM'].z);
	rearWingMesh.geometry = rearWingGeometryOrig.clone()
		.translate(-constants['r_CM'].x-constants['r_ra'].x, -constants['r_CM'].y-constants['r_ra'].y, -constants['r_CM'].z-constants['r_ra'].z);
	
	panels.values().forEach(panel => panel.dispose());
	components.splice(4, panels.values().length);
	panels.clear();
	for (const id in msg['panels']) {
		const data = msg['panels'][id];
		const panel = new Panel(id, ui.sceneConfig);
		panel.build(data);
		panels.set(id, panel);
		components.push(panel);
		if (panel.rear)
			raGroup.add(panel);
		else
			bodyGroup.add(panel);
	}
	hull.build(msg['hull']);
	propulsor.build(msg['propulsor']);

	console.log('INFO: build successful');
}

let syncFlag = true;
function telem(msg) {
	ui.simStates.U.u = msg['U'][0];
	ui.simStates.U.v = msg['U'][1];
	ui.simStates.U.w = msg['U'][2];
	ui.simStates.omega.p = msg['omega'][0]*180/Math.PI;
	ui.simStates.omega.q = msg['omega'][1]*180/Math.PI;
	ui.simStates.omega.r = msg['omega'][2]*180/Math.PI;
	ui.simStates.Phi.phi = msg['Phi'][0]*180/Math.PI;
	ui.simStates.Phi.theta = msg['Phi'][1]*180/Math.PI;
	ui.simStates.Phi.psi = msg['Phi'][2]*180/Math.PI;
	states.r.fromArray(msg['r']);
	ui.simStates.r.x = msg['r'][0];
	ui.simStates.r.y = msg['r'][1];
	ui.simStates.r.z = msg['r'][2]*100;
	ui.simStates.psi_ra = msg['psi_ra']*180/Math.PI;
	states.C0b.fromArray(msg['C0b']).transpose();
	states.Cb_ra.fromArray(msg['Cb_ra']).transpose();
	
	bodyGroup.setRotationFromMatrix(new THREE.Matrix4().setFromMatrix3(states.C0b));
	bodyGroup.position.copy(states.r);

	raGroup.setRotationFromMatrix(new THREE.Matrix4().setFromMatrix3(states.Cb_ra));

	for (const id in msg['panels']) panels.get(id).syncTelem(msg['panels'][id], states.Cb_ra);
	for (const id in msg['wing_roots']) wingRoots.get(id).syncTelem(msg['wing_roots'][id]);
	hull.syncTelem(msg['hull']);
	propulsor.syncTelem(msg['propulsor'], states.Cb_ra);
	
	ui.simStates.epsilon = propulsor.epsilon;
	ui.simStates.I = propulsor.I;
	ui.simStates.RPM = propulsor.omega*60/(2*Math.PI);
	ui.updateSimulationStatus(msg['running']);
	
	if (syncFlag) {
		ui.syncControlStates();
		syncFlag = false;
	}

	components.forEach(c => c.syncVisuals());
}

// --- SocketManager ---
const socket = new SocketManager(
	(msg) => {
		if (msg['type'] == 'build') {
			build(msg);
		} else if (msg['type'] == 'telem') {
			telem(msg);
		} else {
			console.log('WARNING: unknown data received', msg)
		}
	},
	(status) => {
		if (status == 'Disconnected') syncFlag = true;
		ui.updateSocketStatus(status)
	}
);
socket.connect(ui.socketParams.url);
ui.callbacks.onConnect = (url) => socket.connect(url);
ui.callbacks.onStateChange = (state, value) => socket.send({ type: 'set', state: state, value: value });
ui.callbacks.onToggleRun = () => socket.send({ type: 'sim' });
ui.callbacks.onStep = () => socket.send({ type: 'step', dt: ui.controlStates.dt });
ui.callbacks.onReset = () => {
	syncFlag = true;
	socket.send({ type: 'reset' });
};

// // --- Body Axes ---
const bodyAxes = new utils.Axes();
bodyGroup.add(bodyAxes);

// --- Fixed Axes ---
const fixedAxes = new utils.Axes();
scene.add(fixedAxes);

window.addEventListener('resize', () => {
	camera.aspect = window.innerWidth / window.innerHeight;
	camera.updateProjectionMatrix()
	renderer.setSize(window.innerWidth, window.innerHeight);
});

const renderloop = () => {
	controls.update();
	renderer.render(scene, camera);
	window.requestAnimationFrame(renderloop);
};

renderloop();