import * as THREE from 'three';

export class Hull {
	constructor(data) {
		this.r_surf = new THREE.Vector3().fromArray(data['r_surf']);

		this.#init();
	}

	#init() {
		this.area_center = new THREE.Vector3();
		this.vol_center = new THREE.Vector3();
		this.F_h = new THREE.Vector3();
		this.M_h = new THREE.Vector3();
		this.F_b = new THREE.Vector3();
		this.M_b = new THREE.Vector3();
		this.Cbw = new THREE.Matrix3();

		this.surfAxes = new THREE.AxesHelper();
		this.surfAxes.setColors('red','green','blue');

		this.surfAxes = new THREE.AxesHelper();
		this.surfAxes.setColors('red','green','blue');
	}

	update(telem) {
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
		this.Cbw.transposeIntoArray(telem['Cbw']);

		this.surf.alpha = telem['surf']['alpha'];
		this.surf.beta = telem['surf']['beta'];
		this.surf.L = telem['surf']['L'];
		this.surf.D = telem['surf']['D'];
		this.surf.F.fromArray(telem['surf']['F_h']);
		this.surf.M.fromArray(telem['surf']['M_h']);
		this.surf.Cbw.transposeIntoArray(telem['surf']['Cbw']);
	}

	dispose() {
		this.subMesh.parent?.remove(this.subMesh);
		this.surfMesh.parent?.remove(this.surfMesh);
		this.subGeom.dispose();
		this.surfGeom.dispose();
		this.subMat.dispose();
		this.surfMat.dispose();
	}
}