import * as THREE from 'three';
import { mkConfig, generateCsv, download } from 'export-to-csv';

export class RunManager {
	elapsed = $state(0);
	inProgress = $state(false);
	usage = $state(0);
	up = new THREE.Vector3(0,0,-1);
	offsetDist = 3;
	backDist = 5;
	constructor(dm,viz) {
		this.dm = dm;
		this.viz = viz;
		this.log = [];
		viz.onRender = () => this.update();
		viz.onTelem = () => this.#updateLog();
	}
	onToggleRun() {
		this.inProgress = !this.inProgress;
		if (this.inProgress) {
			this.viz.targetBuoy = this.viz.farBuoyMesh;
			this.startTime = this.dm.simStates.time;
			this.lastUpdated = this.dm.simStates.time;
			this.elapsed = 0;
			this.turns = 0;
			this.lastCriterion = this.#getCriterion();
			this.usage = 0;
			this.log = [];
		}
	}
	onExportRun() {
		const headers = Object.keys(this.log[0]);
		const csvConfig = mkConfig({ 
			columnHeaders: headers, 
			useKeyAsHeaders: true, 
			filename: `run_${(new Date()).toLocaleString()}` })
		const csvOutput = generateCsv(csvConfig)(this.log);
		download(csvConfig)(csvOutput);
	}
	#updateLog() {
		if (!this.inProgress) return;
		const entry = {
			time: this.dm.simStates.time,
			I: this.dm.simStates.I,
			u: this.dm.simStates.U.u,
			V: this.dm.simStates.V,
		}
		this.log.push(entry);
	}
	onPos(pos) {
		const dir = new THREE.Vector3().copy(this.viz.farBuoyMesh.position).sub(this.viz.nearBuoyMesh.position).normalize();
		const rot = Math.atan2(-dir.y, dir.x);
		const offset = new THREE.Vector3().copy(dir).cross(this.up);
		if (pos.includes('Left')) offset.multiplyScalar(-1);
		offset.multiplyScalar(this.offsetDist).sub(dir.clone().multiplyScalar(this.backDist));
		{
			this.dm.controlStates.r.x = offset.x + this.viz.nearBuoyMesh.position.x;
			this.dm.controlStates.r.y = offset.y + this.viz.nearBuoyMesh.position.y;
			this.dm.callbacks.onStateChange('r', { origin: 'internal', value: this.dm.controlStates.r });
			this.dm.controlStates.Phi.z = Math.PI/2 - rot*180/Math.PI;
			this.dm.callbacks.onStateChange('Phi', { origin: 'internal', value: this.dm.controlStates.Phi });
		}
	}
	#getCurrentDir() {
		return new THREE.Vector3().copy(this.viz.targetBuoy.position)
			.sub((this.viz.targetBuoy == this.viz.nearBuoyMesh? this.viz.farBuoyMesh : this.viz.nearBuoyMesh).position).normalize();
	}
	#getToBodyVec() {
		return new THREE.Vector3().copy(this.viz.bodyGroup.position).sub(this.viz.targetBuoy.position);
	}
	#getCriterion() {
		const dir = this.#getCurrentDir();
		const toBodyDir = this.#getToBodyVec().normalize();
		return toBodyDir.dot(dir);
	}
	update() {
		if (!this.inProgress) return;
		this.elapsed = this.dm.simStates.time - this.startTime;
		this.dt = this.dm.simStates.time-this.lastUpdated;
		this.lastUpdated = this.dm.simStates.time;
		this.usage += this.dt*this.dm.simStates.V*this.dm.simStates.I/3600/this.dm.constants.V_max;
		const criterion = this.#getCriterion();
		let toBodyVec = this.#getToBodyVec();
		if (criterion > 0 && this.lastCriterion <= 0) {
			this.viz.targetBuoy = this.viz.targetBuoy == this.viz.nearBuoyMesh? this.viz.farBuoyMesh : this.viz.nearBuoyMesh;
			this.turns++;
			if (this.turns == 4) this.onToggleRun();
		}
		if (this.dm.sceneConfig.cameraTrack == 'Buoy' && toBodyVec.lengthSq() < this.viz.buoyDelta.lengthSq()) {
			const camZ = this.viz.camera.position.z;
			const bodyToCam = new THREE.Vector3().copy(this.viz.camera.position).sub(this.viz.bodyGroup.position).setComponent(2,0);
			toBodyVec = this.#getToBodyVec().setComponent(2,0).normalize().multiplyScalar(bodyToCam.length());
			toBodyVec.z = camZ;
			this.viz.camera.position.copy(this.viz.bodyGroup.position).setComponent(2,0).add(toBodyVec);
		}
		this.lastCriterion = criterion;
	}
}