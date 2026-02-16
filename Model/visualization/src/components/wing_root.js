import * as THREE from 'three';

import * as utils from '../utils.js'

export class WingRoot extends THREE.Group {
	constructor(config) {
		super();
		this.config = config;

		this.area_center = new THREE.Vector3();
		this.vol_center = new THREE.Vector3();
		this.F_f = new THREE.Vector3();
		this.M_f = new THREE.Vector3();
		this.F_b = new THREE.Vector3();
		this.M_b = new THREE.Vector3();
		this.Cbw = new THREE.Matrix3();

		this.waterAxes = new utils.Axes(0.25);
		this.foilForce = new utils.Arrow();
		this.foilMoment = new utils.Arrow();
		
		this.buoyantForce = new utils.Arrow();
		this.buoyantMoment = new utils.Arrow();

		this.add(this.waterAxes, this.foilForce, this.foilMoment, this.buoyantForce, this.buoyantMoment);
	}
	syncTelem(telem) {
		this.alpha = telem['alpha'];
		this.beta = telem['beta'];
		this.area = telem['area'];
		this.vol = telem['vol'];
		this.area_center.fromArray(telem['area_center']);
		this.vol_center.fromArray(telem['vol_center']);
		this.L = telem['L'];
		this.D = telem['D'];
		this.F_f.fromArray(telem['F_f']);
		this.M_f.fromArray(telem['M_f']);
		this.F_b.fromArray(telem['F_b']);
		this.M_b.fromArray(telem['M_b']);
		this.Cbw.fromArray(telem['Cbw']).transpose();

		this.waterAxes.setRotMat(this.Cbw);
		this.waterAxes.position.copy(this.area_center);
		
		this.foilForce.position.copy(this.area_center);
		this.foilMoment.position.copy(this.area_center);
		
		this.buoyantForce.position.copy(this.vol_center);
		this.buoyantMoment.position.copy(this.vol_center);

		this.foilForce.setPoint(this.F_f.clone());
		this.buoyantForce.setPoint(this.F_b.clone());
		
		this.foilMoment.setPoint(this.M_f.clone());
		this.buoyantMoment.setPoint(this.M_b.clone());
	}
	syncVisuals() {
		this.waterAxes.setScale(this.config.foilAxesScale);

		this.foilForce.setScale(this.config.forceScale);
		this.buoyantForce.setScale(this.config.forceScale);

		this.foilMoment.setScale(this.config.momentScale);
		this.buoyantMoment.setScale(this.config.momentScale);

		this.foilMoment.mat.color.set(this.config.forceColor);
		this.buoyantForce.mat.color.set(this.config.forceColor);

		this.foilMoment.mat.color.set(this.config.momentColor);
		this.buoyantMoment.mat.color.set(this.config.momentColor);
	}
	toggleAxes() {
		this.waterAxes.visible = !this.waterAxes.visible;
	}
	toggleForces() {
		this.foilForce.visible = !this.foilForce.visible;
		this.buoyantForce.visible = !this.buoyantForce.visible;
	}
	toggleMoments() {
		this.foilMoment.visible = !this.foilMoment.visible;
		this.buoyantMoment.visible = !this.buoyantMoment.visible;
	}
	dispose() {
		this.parent?.remove(this);
		this.foilForce.dispose();
		this.buoyantForce.dispose();

		this.foilMoment.dispose();
		this.buoyantMoment.dispose();

		this.waterAxes.dispose();
	}
}