import * as THREE from 'three';

import * as utils from '../utils.js'

export class Propulsor extends THREE.Group {
	constructor(config) {
		super();
		this.config = config;
		this.r_prop = new THREE.Vector3();

		this.propGeom = new THREE.CircleGeometry(1, 16);
		this.propMat = new THREE.MeshBasicMaterial({ color: config.subColor, side: THREE.DoubleSide, visible: false });
		this.propMesh = new THREE.Mesh(this.propGeom, this.propMat);
		this.propMesh.rotation.y = Math.PI/2;
		this.add(this.propMesh);

		this.F = new THREE.Vector3();
		this.M = new THREE.Vector3();
		this.Cra_w = new THREE.Matrix3();

		this.waterAxes = new utils.Axes(0.25);
		this.force = new utils.Arrow();
		this.moment = new utils.Arrow();
		this.submergence = new utils.Arrow(new THREE.Vector3(-1,0,0));

		this.add(this.waterAxes, this.force, this.moment, this.submergence);
	}
	build(data) {
		this.r_prop.fromArray(data['r_prop']);
		this.d = data['d'];

		this.propMesh.scale.setScalar(this.d/2);
		this.propMat.visible = true;

		this.propMesh.position.copy(this.r_prop);

		this.waterAxes.position.copy(this.r_prop);
		this.force.position.copy(this.r_prop);
		this.moment.position.copy(this.r_prop);
		this.submergence.position.copy(this.r_prop)
	}
	syncTelem(telem, Cra_b) {
		this.beta = telem['beta'];
		this.fp = telem['fp'];
		this.I = telem['I'];
		this.n = telem['n'];
		this.V = telem['V'];
		this.T = telem['T'];
		this.Q = telem['Q'];
		this.F.fromArray(telem['F']);
		this.M.fromArray(telem['M']);
		this.Cra_w.fromArray(telem['Cra_w']).transpose();

		this.waterAxes.setRotMat(this.Cra_w);

		this.force.setPoint(this.F.clone().applyMatrix3(Cra_b), this.config.forceScale);
		this.moment.setPoint(this.M.clone().applyMatrix3(Cra_b), this.config.momentScale);
	}
	syncVisuals() {
		this.waterAxes.setScale(this.config.propAxesScale)

		this.force.setScale(this.config.forceScale);
		this.moment.setScale(this.config.momentScale);
		this.submergence.setScale(this.fp*this.config.submergenceScale);

		this.force.mat.color.set(this.config.forceColor);
		this.moment.mat.color.set(this.config.momentColor);
		this.submergence.mat.color.set(this.config.subColor);
		this.propMat.color.set(this.config.surfColor).lerp(new THREE.Color(this.config.subColor), this.fp);
	}
	toggleAxes() {
		this.waterAxes.visible = !this.waterAxes.visible;
	}
	toggleForces() {
		this.force.visible = !this.force.visible;
	}
	toggleMoments() {
		this.moment.visible = !this.moment.visible;
	}
	toggleSubmergence() {
		this.submergence.visible = !this.submergence.visible;
	}
	dispose() {
		this.parent?.remove(this);
		this.foce.dispose();
		this.moment.dispose();
		
		this.waterAxes.dispose();
	}
}