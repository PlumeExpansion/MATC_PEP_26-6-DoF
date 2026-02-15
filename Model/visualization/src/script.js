import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { STLLoader } from "three/addons/loaders/STLLoader.js";

import { UI } from "./ui.js";
import { SocketManager } from "./client.js";

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
const topLight = new THREE.DirectionalLight('white', 1)
const bottomLight = new THREE.DirectionalLight('white', 0.2)
topLight.position.set(2,-2,-2)
bottomLight.position.set(-2,2,2)
scene.add(ambientLight, topLight, bottomLight);
const topLightHelper = new THREE.DirectionalLightHelper(topLight, 0.5);
const bottomLightHelper = new THREE.DirectionalLightHelper(bottomLight, 0.5);
scene.add(topLightHelper, bottomLightHelper)

// --- Waterplane Grid ---
const grid = new THREE.GridHelper(20, 10);
grid.rotation.x = Math.PI / 2;
scene.add(grid);

// --- Panels ---
const bodyGroup = new THREE.Group()

// --- SocketManager ---
const socket = new SocketManager(
	(msg) => {
		if (msg['type'] == 'build') {
			// TODO: build panels
		} else if (msg['type'] == 'telem') {
			// TODO: telem update
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
	}
})

// --- STL Models ---
const loader = new STLLoader();
const hullGeometry = await loader.loadAsync('RBird_Hull_Remesh.stl');
const wingGeometry = await loader.loadAsync('Wing_Applied_Low_Poly.stl');
const rearWingGeometry = await loader.loadAsync('Rear_Wing_Applied_Low_Poly.stl');
const material = new THREE.MeshPhongMaterial({color: 'white'});
const hullMesh = new THREE.Mesh(hullGeometry, material);
const wingMesh = new THREE.Mesh(wingGeometry, material);
const rearWingMesh = new THREE.Mesh(rearWingGeometry, material);

scene.add(hullMesh, wingMesh, rearWingMesh);

// --- Body Axes ---
const bodyAxes = new THREE.AxesHelper();
bodyAxes.setColors('red','green','blue')
bodyGroup.add(bodyAxes);

// --- Fixed Axes ---
const fixedAxes = new THREE.AxesHelper();
fixedAxes.setColors('red','green','blue');
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