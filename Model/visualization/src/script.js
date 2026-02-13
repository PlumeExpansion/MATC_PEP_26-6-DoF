import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { Pane } from "tweakpane";
import { encode } from "@msgpack/msgpack";

/*
function sendControlUpdate(params) {
    // params = { hull: { dragCoef: 0.5 }, activeFoil: 1, command: 'reset' }
    const encoded = encode(params);
    
    if (socket.readyState === WebSocket.OPEN) {
        socket.send(encoded); 
    }
}

// Example: Trigger on Tweakpane change
pane.on('change', (ev) => {
    sendControlUpdate(params);
});

socket.onmessage = async (event) => {
    const buffer = await event.data.arrayBuffer();
    const data = new Float32Array(buffer);

    // Update the existing foilPositions array values
    // We use .set() to copy data from the network array to the geometry array
    foilPositions.set(data.subarray(0, 18));

    // Tell Three.js the data changed
    posAttribute.needsUpdate = true;

    // Update rotation matrix (indices 18 to 26)
    const matData = data.subarray(18, 27);
    updateRotation(matData);
};

import { decode } from "@msgpack/msgpack";

socket.onmessage = async (event) => {
    const buffer = await event.data.arrayBuffer();
    const model = decode(buffer);

    console.log(model.hull.F); // Easy access!
};
*/

const serverPort = 8765

const pane = new Pane();
const scene = new THREE.Scene();
const socket = new WebSocket(`ws://localhost:${serverPort}`);

// add objects to the scene
// const cubeGeometry = new THREE.BoxGeometry(1, 1, 1);
// const cubeMaterial = new THREE.MeshBasicMaterial({ color: "red" });

// const cubeMesh = new THREE.Mesh(cubeGeometry, cubeMaterial);
// scene.add(cubeMesh);

aspect = window.innerWidth / window.innerHeight;
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

camera.position.z = 5;

const canvas = document.querySelector("canvas.threejs");
const renderer = new THREE.WebGLRenderer({canvas: canvas, antialias: true,});
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))

const controls = new OrbitControls(camera, canvas);
controls.enableDamping = true;
// controls.autoRotate = true;

window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix()
  renderer.setSize(window.innerWidth, window.innerHeight);
})

const renderloop = () => {
  controls.update();  renderer.render(scene, camera);
  window.requestAnimationFrame(renderloop);
};

renderloop();


/*
import { Pane } from 'tweakpane';

const socket = new WebSocket('ws://localhost:8765');
const pane = new Pane();

// Tweakpane State
const params = {
    running: true,
    velocity: 0.1,
};

// Toggle Pause/Resume
pane.addBinding(params, 'running', { label: 'Sim Running' })
    .on('change', (ev) => {
        socket.send(json.stringify({
            type: 'control',
            value: ev.value
        }));
    });

// Change Physics Parameters
pane.addBinding(params, 'velocity', { min: 0, max: 1 })
    .on('change', (ev) => {
        socket.send(json.stringify({
            type: 'update_vel',
            value: ev.value
        }));
    });

function sendUpdate(data) {
    // 1. Check if the socket is even alive
    if (socket.readyState === WebSocket.OPEN) {
        // 2. Check if the "outgoing pipe" is full (e.g., more than 1KB waiting)
        if (socket.bufferedAmount === 0) {
            socket.send(JSON.stringify(data));
        } else {
            // Buffer is busy; skip this frame to keep the UI real-time
            console.warn("Network congested, skipping sync frame.");
        }
    }
}

// Create a geometry for the submerged part (4 vertices = 2 triangles)
const submergedGeom = new THREE.BufferGeometry();
const submergedMat = new THREE.MeshBasicMaterial({ color: 0xffa500, side: THREE.DoubleSide });
const submergedMesh = new THREE.Mesh(submergedGeom, submergedMat);

// Add it to your boat group so it follows body-frame coordinates
boatGroup.add(submergedMesh);

function updateFoil(coords) {
    // coords = [botL, botR, midL, midR, topL, topR]
    const vertices = new Float32Array([
        ...coords.botL, ...coords.botR, ...coords.midL, // Triangle 1
        ...coords.botR, ...coords.midR, ...coords.midL  // Triangle 2
    ]);
    
    submergedGeom.setAttribute('position', new THREE.BufferAttribute(vertices, 3));
    submergedGeom.attributes.position.needsUpdate = true;
}

// Assuming data.matrix is a 9-element array from Python (column-major)
const m4 = new THREE.Matrix4();
m4.set(
    data.matrix[0], data.matrix[3], data.matrix[6], 0,
    data.matrix[1], data.matrix[4], data.matrix[7], 0,
    data.matrix[2], data.matrix[5], data.matrix[8], 0,
    0, 0, 0, 1
);

boatGroup.quaternion.setFromRotationMatrix(m4);

// Global World Axes
scene.add(new THREE.AxesHelper(5));

// Local Body Axes (attach to the boat)
const bodyAxes = new THREE.AxesHelper(2);
boatGroup.add(bodyAxes);


*/