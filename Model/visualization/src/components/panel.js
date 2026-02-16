import * as THREE from 'three';

import * as utils from '../utils.js'

export class Panel extends THREE.Group {
	constructor(id, config) {
		super();
		this.panelId = id;
		this.config = config;
		this.r_qc_fC = new THREE.Vector3();
		this.Cbw = new THREE.Matrix3();
		this.r_LE_1 = new THREE.Vector3();
		this.r_LE_2 = new THREE.Vector3();
		this.r_TE_1 = new THREE.Vector3();
		this.r_TE_2 = new THREE.Vector3();

		this.F = new THREE.Vector3();
		this.M = new THREE.Vector3();

		this.subGeom = new THREE.BufferGeometry();
		this.surfGeom = new THREE.BufferGeometry();
		this.subVerts = new Float32Array(18);
		this.surfVerts = new Float32Array(18);
		this.subGeom.setAttribute('position', new THREE.BufferAttribute(this.subVerts, 3));
		this.surfGeom.setAttribute('position', new THREE.BufferAttribute(this.surfVerts, 3));
		
		this.subMat = new THREE.MeshBasicMaterial({ side: THREE.DoubleSide});
		this.surfMat = new THREE.MeshBasicMaterial({ side: THREE.DoubleSide});
		this.subMesh = new THREE.Mesh(this.subGeom, this.subMat);
		this.surfMesh = new THREE.Mesh(this.surfGeom, this.surfMat);

		this.waterAxes = new utils.Axes(0.25);
		this.submergence = new utils.Arrow();
		this.force = new utils.Arrow();
		this.moment = new utils.Arrow();

		this.add(this.subMesh, this.surfMesh, this.waterAxes, this.submergence, this.force, this.moment);
	}
	build(data) {
		this.r_LE_1.fromArray(data['r_LE_1']);
		this.r_LE_2.fromArray(data['r_LE_2']);
		this.r_TE_1.fromArray(data['r_TE_1']);
		this.r_TE_2.fromArray(data['r_TE_2']);

		this.rear = data['rear'];
		this.norm = new THREE.Vector3().subVectors(this.r_LE_1, this.r_LE_2)
			.cross(new THREE.Vector3().copy(this.r_TE_2).sub(this.r_LE_2)).multiplyScalar(this.panelId.includes('L')? -1 : 1).normalize();
	}
	syncTelem(telem,Cb_ra) {
		this.alpha = telem['alpha'];
		this.beta = telem['beta'];
		this.f = telem['f'];
		this.one_lower = telem['one_lower'];
		this.r_qc_fC.fromArray(telem['r_qc_fC']);
		this.L = telem['L'];
		this.D = telem['D'];
		this.F.fromArray(telem['F']);
		this.M.fromArray(telem['M']);
		this.Cbw.fromArray(telem['Cbw']).transpose();

		if (this.one_lower) {
			this.r_LE_f = new THREE.Vector3().copy(this.r_LE_2).multiplyScalar(this.f).addScaledVector(this.r_LE_1, 1-this.f);
			this.r_TE_f = new THREE.Vector3().copy(this.r_TE_2).multiplyScalar(this.f).addScaledVector(this.r_TE_1, 1-this.f);
			this.#setVerts(this.surfVerts, this.r_LE_f, this.r_TE_f, this.r_TE_2, this.r_LE_2);
			this.#setVerts(this.subVerts, this.r_LE_1, this.r_TE_1, this.r_TE_f, this.r_LE_f);
		} else {
			this.r_LE_f = new THREE.Vector3().copy(this.r_LE_1).multiplyScalar(this.f).addScaledVector(this.r_LE_2, 1-this.f);
			this.r_TE_f = new THREE.Vector3().copy(this.r_TE_1).multiplyScalar(this.f).addScaledVector(this.r_TE_2, 1-this.f);
			this.#setVerts(this.subVerts, this.r_LE_f, this.r_TE_f, this.r_TE_2, this.r_LE_2);
			this.#setVerts(this.surfVerts, this.r_LE_1, this.r_TE_1, this.r_TE_f, this.r_LE_f);
		}

		this.waterAxes.setRotMat(this.Cbw);
		this.waterAxes.position.copy(this.r_qc_fC);
		
		this.submergence.position.copy(this.r_qc_fC);
		this.force.position.copy(this.r_qc_fC);
		this.moment.position.copy(this.r_qc_fC);

		this.submergence.setPoint(this.norm, this.f*this.config.submergenceScale);
		if (this.rear) {
			this.force.setPoint(this.F.clone().applyMatrix3(Cb_ra));
			this.moment.setPoint(this.M.clone().applyMatrix3(Cb_ra));
		} else {
			this.force.setPoint(this.F.clone());
			this.moment.setPoint(this.M.clone());
		}

		this.subGeom.attributes.position.needsUpdate = true;
		this.surfGeom.attributes.position.needsUpdate = true;
		this.subGeom.computeBoundingSphere();
		this.surfGeom.computeBoundingSphere();
	}
	syncVisuals() {
		this.waterAxes.setScale(this.config.foilAxesScale);
		this.subMat.color.set(this.config.subColor);
		this.surfMat.color.set(this.config.surfColor);

		this.force.setScale(this.config.forceScale);
		this.moment.setScale(this.config.momentScale);
		this.submergence.setScale(this.f*this.config.submergenceScale);

		this.submergence.mat.color.set(this.config.subColor);
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
	toggleSubmergence() {
		this.submergence.visible = !this.submergence.visible;
	}
	toggleSubmerged() {
		this.subMesh.visible = !this.subMesh.visible;
	}
	toggleSurfaced() {
		this.surfMesh.visible = !this.surfMesh.visible;
	}
	#setVerts(verts,r1,r2,r3,r4) {
		verts[0] = r1.x; verts[1] = r1.y; verts[2] = r1.z;
		verts[3] = r2.x; verts[4] = r2.y; verts[5] = r2.z;
		verts[6] = r3.x; verts[7] = r3.y; verts[8] = r3.z;
		
		verts[9]  = r3.x; verts[10] = r3.y; verts[11] = r3.z;
		verts[12] = r4.x; verts[13] = r4.y; verts[14] = r4.z;
		verts[15] = r1.x; verts[16] = r1.y; verts[17] = r1.z;
	}
	dispose() {
		this.parent?.remove(this);
		this.subGeom.dispose();
		this.surfGeom.dispose();

		this.subMat.dispose();
		this.surfMat.dispose();
	}
}