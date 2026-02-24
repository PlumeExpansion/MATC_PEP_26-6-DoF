import * as THREE from 'three';

export class RunManager {
	elapsed = $state(0);
	inProgress = $state(false);
	up = new THREE.Vector3(0,0,-1);
	offsetDist = 3;
	backDist = 5;
	constructor(dm,viz) {
		this.dm = dm;
		this.viz = viz;
		viz.onRender = () => this.update();
	}
	onToggleRun() {
		this.inProgress = !this.inProgress;
		if (this.inProgress) {
			this.viz.targetBuoy = this.viz.nearBuoyMesh;
			this.startTime = this.dm.simStates.time;
			this.elapsed = 0;
			this.turns = 0;
		}
	}
	#getDir() {
		return new THREE.Vector3().copy(this.viz.farBuoyMesh.position).sub(this.viz.nearBuoyMesh.position).normalize();
	}
	onPos(pos) {
		const dir = this.#getDir();
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
	update() {
		if (!this.inProgress) return;
		this.elapsed = this.dm.simStates.time - this.startTime;
		const dir = this.#getDir();
		//TODO: turn count logic
		// if ()
	}
}