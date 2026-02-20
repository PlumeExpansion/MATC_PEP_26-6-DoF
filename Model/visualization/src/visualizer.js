import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { STLLoader } from "three/addons/loaders/STLLoader.js";

import { UI } from "./ui.js";
import { SocketManager } from "./socket_manager.js";
import { Hull } from "./components/hull.js";
import { Panel } from "./components/panel.js";
import { WingRoot } from "./components/wing_root.js";
import { Propulsor } from "./components/propulsor.js";
import { Waterplane } from "./waterplane.js";
import * as utils from './utils.js';

// --- Scene Setup ---
const canvas = document.querySelector("canvas.threejs");
const renderer = new THREE.WebGLRenderer({canvas: canvas, antialias: true,});
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))

const scene = new THREE.Scene();

let aspectRatio = window.innerWidth / window.innerHeight;
const camera = new THREE.PerspectiveCamera(35, aspectRatio,0.1,500);

// const aspectRatio = window.innerWidth / window.innerHeight;
// const camera = new THREE.OrthographicCamera(
//   -1 * aspectRatio,
//   1 * aspectRatio,
//   1,
//   -1,
//   0.1,
//   200
// );

camera.defaultPosition = new THREE.Vector3(5, -3, -2);
camera.position.copy(camera.defaultPosition);
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
ui.callbacks.onRefocusCamera = () => {
	const target = new THREE.Vector3(ui.simStates.r.x, ui.simStates.r.y, ui.simStates.r.z/100)
	camera.position.copy(target).add(camera.defaultPosition);
	camera.lookAt(target);
	controls.target.copy(target);
	controls.update();
}

// --- Waterplane Grid ---
const waterplane = new Waterplane(ui.sceneConfig, 20, 20, 0.01, 2);
scene.add(waterplane);

// --- STL Models ---
const bodyGroup = new THREE.Group();
const raGroup = new THREE.Group();
bodyGroup.add(raGroup);
bodyGroup.oldPos = new THREE.Vector3();
scene.add(bodyGroup);

const loader = new STLLoader();
const hullGeometryOrig = await loader.loadAsync('RBird_Hull_Remesh.stl');
const wingGeometryOrig = await loader.loadAsync('Wing_Applied_Low_Poly.stl');
const rearWingGeometryOrig = await loader.loadAsync('Rear_Wing_Applied_Low_Poly.stl');
const material = new THREE.MeshPhongMaterial({color: 'white', transparent: true, opacity: ui.sceneConfig.stlOpacity });
const hullMesh = new THREE.Mesh(hullGeometryOrig, material);
const wingMesh = new THREE.Mesh(wingGeometryOrig, material);
const rearWingMesh = new THREE.Mesh(rearWingGeometryOrig, material);

bodyGroup.add(hullMesh, wingMesh);
raGroup.add(rearWingMesh);

ui.callbacks.onToggleHull = () => hullMesh.visible = !hullMesh.visible;
ui.callbacks.onToggleWings = () => wingMesh.visible = !wingMesh.visible;
ui.callbacks.onToggleRearWings = () => rearWingMesh.visible = !rearWingMesh.visible;
ui.callbacks.onStlOpacity = () => material.opacity = ui.sceneConfig.stlOpacity;

ui.callbacks.onToggleGrid = () => waterplane.toggleGrid();
ui.callbacks.onToggleWaterplane = () => waterplane.toggleWaterplane();

// --- Components ---
const constants = {
	r_CM: new THREE.Vector3(),
	r_ra: new THREE.Vector3()
};
const states = {
	r: new THREE.Vector3(),
	C0b: new THREE.Matrix3(),
	Cra_b: new THREE.Matrix3()
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

ui.constants = constants;
ui.callbacks.onToggleHullAxes = () => hull.toggleAxes();
ui.callbacks.onToggleFoilAxes = () => {
	panels.forEach(panel => panel.toggleAxes());
	wingRoots.values().forEach(wr => wr.toggleAxes());
}
ui.callbacks.onTogglePropulsorAxes = () => propulsor.toggleAxes();
ui.callbacks.onVisuals = () => {
	components.forEach(c => c.syncVisuals());
	waterplane.syncVisuals();
};
ui.callbacks.onToggleForces = () => components.forEach(c => c.toggleForces());
ui.callbacks.onToggleMoments = () => components.forEach(c => c.toggleMoments());
ui.callbacks.onToggleSubmerged = () => panels.forEach(p => p.toggleSubmerged());
ui.callbacks.onToggleSurfaced = () => panels.forEach(p => p.toggleSurfaced());
ui.callbacks.onToggleSubmergence = () => {
	panels.forEach(p => p.toggleSubmergence());
	propulsor.toggleSubmergence();
};

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

	constants.V_max = msg['V_max'];
	constants.psi_ra_max = msg['psi_ra_max']*180/Math.PI;

	ui.setBuildTelem(msg);

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
	states.Cra_b.fromArray(msg['Cra_b']).transpose();
	states.Cb_ra = states.Cra_b.clone().transpose();
	
	bodyGroup.oldPos.copy(bodyGroup.position)
	bodyGroup.setRotationFromMatrix(new THREE.Matrix4().setFromMatrix3(states.C0b));
	bodyGroup.position.copy(states.r);

	raGroup.setRotationFromMatrix(new THREE.Matrix4().setFromMatrix3(states.Cb_ra));

	for (const id in msg['panels']) panels.get(id).syncTelem(msg['panels'][id], states.Cra_b);
	for (const id in msg['wing_roots']) wingRoots.get(id).syncTelem(msg['wing_roots'][id]);
	hull.syncTelem(msg['hull']);
	propulsor.syncTelem(msg['propulsor'], states.Cra_b);
	
	ui.simStates.V = propulsor.V;
	ui.simStates.I = propulsor.I;
	ui.simStates.RPM = propulsor.n*60;
	ui.simStates.rate = msg['rate'];
	ui.simStates.method = msg['method'];
	ui.setMethod(msg['method'])
	ui.updateSimulationStatus(msg['running']);
	
	if (syncFlag) {
		ui.syncControlStates();
		ui.syncInputs();
		syncFlag = false;
	}

	if (ui.sceneConfig.cameraFollow) camera.position.sub(bodyGroup.oldPos.sub(bodyGroup.position));

	waterplane.updateGrid(states.r);
	components.forEach(c => c.syncVisuals());
	waterplane.syncVisuals();
}

ui.callbacks.onPause = () => {
	ui.syncControlStates();
	ui.syncInputs();
}

// --- SocketManager ---
const socket = new SocketManager(
	(msg) => {
		ui.setTelem(msg);
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
ui.callbacks.onStateChange = (state, value) => {
	socket.send({ type: 'set', state: state, value: value });
};
ui.callbacks.onToggleRun = () => socket.send({ type: 'sim' });
ui.callbacks.onStep = () => {
	syncFlag = true;
	socket.send({ type: 'step', dt: Math.pow(10,ui.controlStates.log_dt) });
};
ui.callbacks.onExport = () => socket.send({ type: 'export' })
ui.callbacks.onReset = () => {
	syncFlag = true;
	socket.send({ type: 'reset' });
};
ui.callbacks.onReinit = () => {
	syncFlag = true;
	socket.send({ type: 'reinit' });
}

// --- Coordinate Frame ---
const fixedFrame = new utils.Axes();
scene.add(fixedFrame);
const bodyFrame = new utils.Axes();
bodyGroup.add(bodyFrame);
const rearAxleFrame = new utils.Axes();
raGroup.add(rearAxleFrame);

ui.callbacks.onToggleFixedFrame = () => fixedFrame.visible = !fixedFrame.visible;
ui.callbacks.onToggleBodyFrame = () => bodyFrame.visible = !bodyFrame.visible;
ui.callbacks.onToggleRearAxleFrame = () => rearAxleFrame.visible = !rearAxleFrame.visible;

window.addEventListener('resize', () => {
	camera.aspect = window.innerWidth / window.innerHeight;
	camera.updateProjectionMatrix()
	renderer.setSize(window.innerWidth, window.innerHeight);
});

const renderloop = () => {
	if (ui.sceneConfig.cameraTarget || ui.sceneConfig.cameraFollow) controls.target.copy(bodyGroup.position);
	controls.update();
	try {
		renderer.render(scene, camera);
	} catch (error) {
		console.error("ERROR: render error:", error);
	}
	window.requestAnimationFrame(renderloop);
};

renderloop();