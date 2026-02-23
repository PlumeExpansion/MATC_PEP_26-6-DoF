import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { STLLoader } from "three/addons/loaders/STLLoader.js";

import { Hull } from "./components/hull.js";
import { Panel } from "./components/panel.js";
import { WingRoot } from "./components/wing_root.js";
import { Propulsor } from "./components/propulsor.js";
import { Waterplane } from "./waterplane.js";
import * as utils from './utils.js';

export class Visualizer {
	constructor(tm) {
		this.tm = tm;
		this.syncFlag = true;

		// --- Main Setup ---
		this.canvas = document.querySelector("canvas.threejs");
		this.renderer = new THREE.WebGLRenderer({canvas: this.canvas, antialias: true,});
		this.renderer.setSize(window.innerWidth, window.innerHeight);
		this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

		this.scene = new THREE.Scene();
		this.camera = new THREE.PerspectiveCamera(35, window.innerWidth/window.innerHeight, 0.1, 500);
		this.camera.defaultPosition = new THREE.Vector3(5, -3, -2);
		this.camera.position.copy(this.camera.defaultPosition);
		this.camera.up = new THREE.Vector3(0,0,-1);
		
		window.addEventListener('resize', () => {
			this.camera.aspect = window.innerWidth / window.innerHeight;
			this.camera.updateProjectionMatrix()
			this.renderer.setSize(window.innerWidth, window.innerHeight);
		});

		this.controls = new OrbitControls(this.camera, this.canvas);
		this.controls.enableDamping = true;
		this.controls.zoomSpeed = 2;
		this.controls.zoomToCursor = true;
		
		this.renderloop = () => {
			if (tm.sceneConfig.cameraTarget || tm.sceneConfig.cameraFollow) 
				this.controls.target.copy(this.bodyGroup.position);
			this.controls.update();
			try {
				this.renderer.render(this.scene, this.camera);
			} catch (error) {
				console.error("ERROR: render error:", error);
			}
			window.requestAnimationFrame(this.renderloop);
		};

		// --- Scene Setup ---
		this.waterplane = new Waterplane(this.tm.sceneConfig, 20, 20, 0.01, 2);
		this.scene.add(this.waterplane);
		tm.callbacks.onToggleGrid = () => this.waterplane.toggleGrid();
		tm.callbacks.onToggleWaterplane = () => this.waterplane.toggleWaterplane();
		
		// -- Lights -- 
		this.ambientLight = new THREE.AmbientLight('white', 0.05);
		this.topLight = new THREE.DirectionalLight('white', 1.5);
		this.bottomLight = new THREE.DirectionalLight('white', 0.2);
		this.topLight.position.set(2,-2,-2);
		this.bottomLight.position.set(-2,2,2);
		this.scene.add(this.ambientLight, this.topLight, this.bottomLight);
		this.topLightHelper = new THREE.DirectionalLightHelper(this.topLight, 0.5);
		this.bottomLightHelper = new THREE.DirectionalLightHelper(this.bottomLight, 0.5);
		this.scene.add(this.topLightHelper, this.bottomLightHelper);
		
		tm.callbacks.onToggleLightHelpers = () => {
			this.topLightHelper.visible = !this.topLightHelper.visible;
			this.bottomLightHelper.visible = !this.bottomLightHelper.visible;
		};
		tm.callbacks.onRefocusCamera = () => {
			const target = new THREE.Vector3(tm.simStates.r.x, tm.simStates.r.y, tm.simStates.r.z/100)
			this.camera.position.copy(target).add(this.camera.defaultPosition);
			this.camera.lookAt(target);
			this.controls.target.copy(target);
			this.controls.update();
		}

		// -- Groups --
		this.bodyGroup = new THREE.Group();
		this.raGroup = new THREE.Group();
		this.bodyGroup.add(this.raGroup);
		this.bodyGroup.oldPos = new THREE.Vector3();
		this.scene.add(this.bodyGroup);

		// -- Coordinate Frames --
		this.fixedFrame = new utils.Axes();
		this.scene.add(this.fixedFrame);
		this.bodyFrame = new utils.Axes();
		this.bodyGroup.add(this.bodyFrame);
		this.rearAxleFrame = new utils.Axes();
		this.raGroup.add(this.rearAxleFrame);

		tm.callbacks.onToggleFixedFrame = () => this.fixedFrame.visible = !this.fixedFrame.visible;
		tm.callbacks.onToggleBodyFrame = () => this.bodyFrame.visible = !this.bodyFrame.visible;
		tm.callbacks.onToggleRearAxleFrame = () => this.rearAxleFrame.visible = !this.rearAxleFrame.visible;

		// --- Model Setup ---
		this.panels = new Map();
		this.wingRoots = new Map([
			['0', new WingRoot(tm.sceneConfig)],
			['1', new WingRoot(tm.sceneConfig)]
		]);
		this.#loadSTL();
		this.hull = new Hull(tm.sceneConfig);
		this.propulsor = new Propulsor(tm.sceneConfig);
		this.bodyGroup.add(this.hull, this.wingRoots.get('0'), this.wingRoots.get('1'));
		this.raGroup.add(this.propulsor);
		this.components = [this.hull, this.propulsor, this.wingRoots.get('0'), this.wingRoots.get('1')];

		tm.callbacks.onToggleHullAxes = () => this.hull.toggleAxes();
		tm.callbacks.onToggleFoilAxes = () => {
			this.panels.forEach(panel => panel.toggleAxes());
			this.wingRoots.values().forEach(wr => wr.toggleAxes());
		}
		tm.callbacks.onTogglePropulsorAxes = () => this.propulsor.toggleAxes();
		tm.callbacks.onVisuals = () => {
			this.components.forEach(c => c.syncVisuals());
			this.waterplane.syncVisuals();
		};
		tm.callbacks.onToggleForces = () => this.components.forEach(c => c.toggleForces());
		tm.callbacks.onToggleMoments = () => this.components.forEach(c => c.toggleMoments());
		tm.callbacks.onToggleSubmerged = () => this.panels.forEach(p => p.toggleSubmerged());
		tm.callbacks.onToggleSurfaced = () => this.panels.forEach(p => p.toggleSurfaced());
		tm.callbacks.onToggleSubmergence = () => {
			this.panels.forEach(p => p.toggleSubmergence());
			this.propulsor.toggleSubmergence();
		};
	}
	async #loadSTL() {
		const loader = new STLLoader();
		this.hullGeometryOrig = await loader.loadAsync('RBird_Hull_Remesh.stl');
		this.wingGeometryOrig = await loader.loadAsync('Wing_Applied_Low_Poly.stl');
		this.rearWingGeometryOrig = await loader.loadAsync('Rear_Wing_Applied_Low_Poly_RA_Origin.stl');
		this.stlMaterial = new THREE.MeshPhongMaterial({
			color: 'white', 
			transparent: true, 
			opacity: this.tm.sceneConfig.stlOpacity
		});
		this.hullMesh = new THREE.Mesh(this.hullGeometryOrig, this.stlMaterial);
		this.wingMesh = new THREE.Mesh(this.wingGeometryOrig, this.stlMaterial);
		this.rearWingMesh = new THREE.Mesh(this.rearWingGeometryOrig, this.stlMaterial);

		this.bodyGroup.add(this.hullMesh, this.wingMesh);
		this.raGroup.add(this.rearWingMesh);
		this.tm.callbacks.onToggleHull = () => this.hullMesh.visible = !this.hullMesh.visible;
		this.tm.callbacks.onToggleWings = () => this.wingMesh.visible = !this.wingMesh.visible;
		this.tm.callbacks.onToggleRearWings = () => this.rearWingMesh.visible = !this.rearWingMesh.visible;
		this.tm.callbacks.onStlOpacity = () => this.stlMaterial.opacity = this.tm.sceneConfig.stlOpacity;
	}
	build(msg) {
		this.raGroup.position.copy(this.tm.constants.r_ra);

		this.hullMesh.position.copy(this.tm.constants.r_CM).multiplyScalar(-1);
		this.wingMesh.position.copy(this.tm.constants.r_CM).multiplyScalar(-1);
		
		this.panels.values().forEach(panel => panel.dispose());
		this.components.splice(4, this.panels.values().length);
		this.panels.clear();
		for (const id in msg['panels']) {
			const data = msg['panels'][id];
			const panel = new Panel(id, this.tm.sceneConfig);
			panel.build(data);
			this.panels.set(id, panel);
			this.components.push(panel);
			if (panel.rear)
				this.raGroup.add(panel);
			else
				this.bodyGroup.add(panel);
		}
		this.hull.build(msg['hull']);
		this.propulsor.build(msg['propulsor']);

		console.log('INFO: build successful');
	}
	telem(msg) {
		this.bodyGroup.oldPos.copy(this.bodyGroup.position)
		this.bodyGroup.setRotationFromMatrix(new THREE.Matrix4().setFromMatrix3(this.tm.states.C0b));
		this.bodyGroup.position.copy(this.tm.states.r);

		this.raGroup.setRotationFromMatrix(new THREE.Matrix4().setFromMatrix3(this.tm.states.Cb_ra));

		for (const id in msg['panels']) this.panels.get(id).syncTelem(msg['panels'][id], this.tm.states.Cra_b);
		for (const id in msg['wing_roots']) this.wingRoots.get(id).syncTelem(msg['wing_roots'][id]);
		this.hull.syncTelem(msg['hull']);
		this.propulsor.syncTelem(msg['propulsor'], this.tm.states.Cra_b);
		
		this.tm.simStates.V = this.propulsor.V;
		this.tm.simStates.I = this.propulsor.I;
		this.tm.simStates.RPM = this.propulsor.n*60;
		this.tm.simStates.rate = msg['rate'];
		this.tm.simStates.method = msg['method'];
		this.tm.setMethod(msg['method'])
		this.tm.updateSimulationStatus(msg['running']);
		
		if (this.syncFlag) {
			this.tm.syncControlStates();
			this.tm.syncInputs();
			this.syncFlag = false;
		}

		if (this.tm.sceneConfig.cameraFollow) this.camera.position.sub(this.bodyGroup.oldPos.sub(this.bodyGroup.position));

		this.waterplane.updateGrid(this.tm.states.r);
		this.components.forEach(c => c.syncVisuals());
		this.waterplane.syncVisuals();
	}
}