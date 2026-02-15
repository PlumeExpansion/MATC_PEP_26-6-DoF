import * as THREE from 'three';
import { vec3, mat3 } from 'gl-matrix';

const subColor = 'orange'
const surfColor = 'white'

export class Panel {
	constructor(id,data) {
		this.id = id;
		this.r_LE_1 = new THREE.Vector3(data['r_LE_1']);
		this.r_LE_2 = new THREE.Vector3(data['r_LE_2']);
		this.r_TE_1 = new THREE.Vector3(data['r_TE_1']);
		this.r_TE_2 = new THREE.Vector3(data['r_TE_2']);

		this.#init();
	}

	#init() {
		this.subGeom = new THREE.BufferGeometry();
		this.surfGeom = new THREE.BufferGeometry();
		this.subVerts = new Float32Array(18);
		this.surfVerts = new Float32Array(18);
		this.subGeom.setAttribute('position', new THREE.BufferAttribute(this.subVerts, 3));
		this.surfGeom.setAttribute('position', new THREE.BufferAttribute(this.surfVerts, 3));
		
		this.subMat = new THREE.MeshBasicMaterial({ color: subColor, side: THREE.DoubleSide});
		this.surfMat = new THREE.MeshBasicMaterial({ color: surfColor, side: THREE.DoubleSide});
		this.subMesh = new THREE.Mesh(this.subGeom, this.subMat);
		this.surfMesh = new THREE.Mesh(this.surfGeom, this.surfMat);

		this.r_qc_fC_body = new THREE.Vector3();
	}

	update(data) {
		this.alpha = data['alpha']
		this.beta = data['beta']
		this.f = data['f']
		this.one_lower = data['one_lower']
		this.r_qc_fC_body.fromArray(data['r_qc_fC_body'])
		this.L = data['L']
		this.D = data['D']
		this.F = data['F']
		this.M = data['M']
		this.Cbf = data['Cbf']

		this.r_LE_f = this.r_LE_1.multiplyScalar(f).addScaledVector(this.r_LE_2, 1-f)
		this.r_TE_f = this.r_TE_1.multiplyScalar(f).addScaledVector(this.r_TE_2, 1-f)

		this.#setVerts(this.subVerts, this.r_LE_f, this.r_TE_f, this.r_TE_2, this.r_LE_2)
		this.#setVerts(this.surfVerts, this.r_LE_1, this.r_TE_1, this.r_TE_f, this.r_LE_f)

		if (this.one_lower) {
			this.subMat.color = surfColor
			this.surfMat.color = subColor
		} else {
			this.subMat.color = subColor
			this.surfMat.color = surfColor
		}

		this.subGeom.attributes.position.needsUpdate = true;
		this.surfGeom.attributes.position.needsUpdate = true;
		this.subGeom.computeBoundingSphere();
		this.surfGeom.computeBoundingSphere();
	}

	#setVerts(verts,r1,r2,r3,r4) {
		verts[0] = r1.x; verts[1] = r1.y; verts[2] = r1.z;
		verts[3] = r2.x; verts[4] = r2.y; verts[5] = r2.z;
		verts[6] = r3.x; verts[7] = r3.y; verts[8] = r3.z;
		
		verts[9]  = r2.x; verts[10] = r2.y; verts[11] = r2.z;
		verts[12] = r4.x; verts[13] = r4.y; verts[14] = r4.z;
		verts[15] = r3.x; verts[16] = r3.y; verts[17] = r3.z;
	}

	getMesh() {
		return [this.subMesh, this.surfMesh];
	}
}