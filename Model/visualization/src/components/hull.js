import * as THREE from 'three';

import * as utils from '../utils.js'

export class Hull extends THREE.Group {
	constructor(config) {
		super();
		this.config = config;
		this.r_surf = new THREE.Vector3();

		this.area_center = new THREE.Vector3();
		this.vol_center = new THREE.Vector3();
		this.F_h = new THREE.Vector3();
		this.M_h = new THREE.Vector3();
		this.F_b = new THREE.Vector3();
		this.M_b = new THREE.Vector3();
		this.Cbw = new THREE.Matrix3();

		this.surf = {};
		this.surf.F = new THREE.Vector3();
		this.surf.M = new THREE.Vector3();
		this.surf.Cbw = new THREE.Matrix3();

		this.hullAxes = new utils.Axes(0.5);
		this.surfAxes = new utils.Axes(0.5);

		this.hullForce = new utils.Arrow();
		this.hullMoment = new utils.Arrow();

		this.buoyantForce = new utils.Arrow();
		this.buoyantMoment = new utils.Arrow();

		this.surfForce = new utils.Arrow();
		this.surfMoment = new utils.Arrow();

		this.add(this.hullAxes, this.surfAxes, this.hullForce, this.hullMoment,
			this.buoyantForce, this.buoyantMoment, this.surfForce, this.surfMoment
		);
	}
	build(data) {
		this.r_surf.fromArray(data['r_surf']);

		this.surfAxes.position.copy(this.r_surf);
		this.surfForce.position.copy(this.r_surf);
		this.surfMoment.position.copy(this.r_surf);
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
		this.F_h.fromArray(telem['F_h']);
		this.M_h.fromArray(telem['M_h']);
		this.F_b.fromArray(telem['F_b']);
		this.M_b.fromArray(telem['M_b']);
		this.Cbw.fromArray(telem['Cbw']).transpose();

		this.surf.alpha = telem['surf']['alpha'];
		this.surf.beta = telem['surf']['beta'];
		this.surf.L = telem['surf']['L'];
		this.surf.D = telem['surf']['D'];
		this.surf.F.fromArray(telem['surf']['F']);
		this.surf.M.fromArray(telem['surf']['M']);
		this.surf.Cbw.fromArray(telem['surf']['Cbw']).transpose();

		this.hullAxes.setRotMat(this.Cbw);
		this.surfAxes.setRotMat(this.surf.Cbw);
		this.hullAxes.position.copy(this.area_center);
		
		this.hullForce.position.copy(this.area_center);
		this.hullMoment.position.copy(this.area_center);
		
		this.buoyantForce.position.copy(this.vol_center);
		this.buoyantMoment.position.copy(this.vol_center);

		this.hullForce.setPoint(this.F_h.clone());
		this.buoyantForce.setPoint(this.F_b.clone());
		this.surfForce.setPoint(this.surf.F.clone());
		
		this.hullMoment.setPoint(this.M_h.clone());
		this.buoyantMoment.setPoint(this.M_b.clone());
		this.surfMoment.setPoint(this.surf.M.clone());
	}
	syncVisuals() {
		this.hullAxes.setScale(this.config.hullAxesScale);
		this.surfAxes.setScale(this.config.hullAxesScale);

		this.hullForce.setScale(this.config.forceScale);
		this.buoyantForce.setScale(this.config.forceScale);
		this.surfForce.setScale(this.config.forceScale);

		this.hullMoment.setScale(this.config.momentScale);
		this.buoyantMoment.setScale(this.config.momentScale);
		this.surfMoment.setScale(this.config.momentScale);

		this.hullForce.mat.color.set(this.config.forceColor);
		this.buoyantForce.mat.color.set(this.config.forceColor);
		this.surfForce.mat.color.set(this.config.forceColor);

		this.hullMoment.mat.color.set(this.config.momentColor);
		this.buoyantMoment.mat.color.set(this.config.momentColor);
		this.surfMoment.mat.color.set(this.config.momentColor);
	}
	toggleAxes() {
		this.hullAxes.visible = !this.hullAxes.visible;
		this.surfAxes.visible = !this.surfAxes.visible;
	}
	toggleForces() {
		this.hullForce.visible = !this.hullForce.visible;
		this.buoyantForce.visible = !this.buoyantForce.visible;
		this.surfForce.visible = !this.surfForce.visible;
	}
	toggleMoments() {
		this.hullMoment.visible = !this.hullMoment.visible;
		this.buoyantMoment.visible = !this.buoyantMoment.visible;
		this.surfMoment.visible = !this.surfMoment.visible;
	}
	dispose() {
		this.parent?.remove(this);
		this.hullForce.dispose();
		this.buoyantForce.dispose();
		this.surfForce.dispose();

		this.hullMoment.dispose();
		this.buoyantMoment.dispose();
		this.surfMoment.dispose();

		this.hullAxes.dispose();
		this.surfAxes.dispose();
	}
}