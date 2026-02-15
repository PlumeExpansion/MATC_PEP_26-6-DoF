import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { STLLoader } from "three/addons/loaders/STLLoader.js";

import { UI } from "./ui.js";
import { SocketManager } from "./socket_manager.js";
import { Panel } from "./components/panel.js";
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

// --- Waterplane Grid ---
const grid = new THREE.GridHelper(20, 10);
grid.rotation.x = Math.PI / 2;
scene.add(grid);

// --- STL Models ---
const loader = new STLLoader();
const hullGeometryOrig = await loader.loadAsync('RBird_Hull_Remesh.stl');
const wingGeometryOrig = await loader.loadAsync('Wing_Applied_Low_Poly.stl');
const rearWingGeometryOrig = await loader.loadAsync('Rear_Wing_Applied_Low_Poly.stl');
const material = new THREE.MeshPhongMaterial({color: 'white'});
const hullMesh = new THREE.Mesh(hullGeometryOrig, material);
const wingMesh = new THREE.Mesh(wingGeometryOrig, material);
const rearWingMesh = new THREE.Mesh(rearWingGeometryOrig, material);

scene.add(hullMesh, wingMesh, rearWingMesh);

// --- Panels ---
const bodyGroup = new THREE.Group();
const raGroup = new THREE.Group();
bodyGroup.add(raGroup);
const constants = new Map();
const panels = new Map();
scene.add(bodyGroup);
scene.add(raGroup);

function build(msg) {
	constants['r_CM'] = new THREE.Vector3().fromArray(msg['r_CM']);
	constants['r_ra'] = new THREE.Vector3().fromArray(msg['r_ra']);
	raGroup.position.set(constants['r_ra'].x, constants['r_ra'].y, constants['r_ra'].z);
	hullMesh.geometry = hullGeometryOrig.clone().translate(-constants['r_CM'].x, -constants['r_CM'].y, -constants['r_CM'].z);
	wingMesh.geometry = wingGeometryOrig.clone().translate(-constants['r_CM'].x, -constants['r_CM'].y, -constants['r_CM'].z);
	rearWingMesh.geometry = rearWingGeometryOrig.clone().translate(-constants['r_CM'].x, -constants['r_CM'].y, -constants['r_CM'].z);
	panels.values().forEach(panel => panel.dispose());
	panels.clear();
	for (const id in msg['panels']) {
		const params = msg['panels'][id];
		const panel = new Panel(id, params);
		panels.set(id, panel);
		panel.getMesh().forEach(mesh => {
			// scene.add(mesh);
			if (panel.rear)
				raGroup.add(mesh);
			else
				bodyGroup.add(mesh);
		});
	}
	console.log('INFO: build successful');
}

function telem(msg) {
	for (const id in msg['panels']) {
		panels.get(id).update(msg['panels'][id])
	}
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
	(status) => ui.updateSocketStatus(status)
);

// --- UI ---
const ui = new UI({
	onConnect: (url) => socket.connect(url),
	onToggleLightHelpers: () => {
		topLightHelper.visible = !topLightHelper.visible;
		bottomLightHelper.visible = !bottomLightHelper.visible;
	},
	onToggleHull: () => hullMesh.visible = !hullMesh.visible,
	onToggleWings: () => wingMesh.visible = !wingMesh.visible,
	onToggleRearWings: () => rearWingMesh.visible = !rearWingMesh.visible
})
socket.connect(ui.params.url);

// --- Body Axes ---
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