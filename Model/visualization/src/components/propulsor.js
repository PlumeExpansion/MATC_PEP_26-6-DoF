import * as THREE from 'three';

import * as utils from '../utils.js'

export class Propulsor extends THREE.Group {
	constructor(config) {
		super();
		this.config = config;
		this.r_prop = new THREE.Vector3();

		this.F = new THREE.Vector3();
		this.M = new THREE.Vector3();
		this.Cra_w = new THREE.Matrix3();

		this.waterAxes = new utils.Axes(0.25);
		this.force = new utils.Arrow();
		this.moment = new utils.Arrow();

		this.add(this.waterAxes, this.force, this.moment);
	}
	build(data) {
		this.r_prop.fromArray(data['r_prop']);
		console.log(this.r_prop)

		this.waterAxes.position.copy(this.r_prop);
		this.force.position.copy(this.r_prop);
		this.moment.position.copy(this.r_prop);
	}
	syncTelem(telem, Cb_ra) {
		this.beta = telem['beta'];
		this.fp = telem['fp'];
		this.I = telem['I'];
		this.omega = telem['omega'];
		this.epsilon = telem['epsilon'];
		this.T = telem['T'];
		this.Q = telem['Q'];
		this.F.fromArray(telem['F']);
		this.M.fromArray(telem['M']);
		this.Cra_w.fromArray(telem['Cra_w']).transpose();

		this.waterAxes.setRotMat(this.Cra_w);

		this.force.setPoint(this.F.clone().applyMatrix3(Cb_ra));
		this.moment.setPoint(this.M.clone().applyMatrix3(Cb_ra));
	}
	syncVisuals() {
		this.waterAxes.setScale(this.config.propAxesScale)

		this.force.setScale(this.config.forceScale);
		this.moment.setScale(this.config.momentScale);

		this.force.mat.color.set(this.config.forceColor);
		this.moment.mat.color.set(this.config.momentColor);
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
	dispose() {
		this.parent?.remove(this);
		this.foce.dispose();
		this.moment.dispose();
		
		this.waterAxes.dispose();
	}
}