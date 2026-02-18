import * as THREE from 'three'

export class Axes extends THREE.Group {
	constructor(scale = 1) {
		super();
		this.scale.set(scale, scale, scale);
		this.xHat = new Arrow(new THREE.Vector3(1,0,0));
		this.yHat = new Arrow(new THREE.Vector3(0,1,0));
		this.zHat = new Arrow(new THREE.Vector3(0,0,1));
		this.add(this.xHat, this.yHat, this.zHat);
		this.setColor('red','lime','blue');
		this.rotMat3 = new THREE.Matrix3();
		this.rotMat4 = new THREE.Matrix4();
	}
	setColor(xCol, yCol, zCol) {
		this.xHat.mat.color.set(xCol);
		this.yHat.mat.color.set(yCol);
		this.zHat.mat.color.set(zCol);
	}
	setFromArray(array) {
		this.rotMat4.setFromMatrix3(this.rotMat3.fromArray(array).transpose());
		this.quaternion.setFromRotationMatrix(this.rotMat4);
	}
	setRotMat(mat3) {
		this.rotMat4.setFromMatrix3(mat3);
		this.quaternion.setFromRotationMatrix(this.rotMat4);
	}
	setScale(scale) {
		this.scale.setScalar(scale);
	}
}

export class Arrow extends THREE.Group {
	constructor(norm = new THREE.Vector3(1,0,0), col = 'white', r = 0.01, rFrac = 1.5, frac = 0.2) {
		super();
		this.coneGeom = new THREE.ConeGeometry();
		this.coneGeom.parameters.radialSegments = 12;
		this.cylinGeom = new THREE.CylinderGeometry();
		this.cylinGeom.parameters.radialSegments = 12;
		this.mat = new THREE.MeshBasicMaterial({ color: col });
		this.coneMesh = new THREE.Mesh(this.coneGeom, this.mat);
		this.cylinMesh = new THREE.Mesh(this.cylinGeom, this.mat);
		this.length = norm.length();
		this.coneMaxScale = this.length*frac;

		this.yHat = new THREE.Vector3(0,1,0);

		this.frac = frac;
		this.rFrac = rFrac;
		this.r = r;
		this.#setRadius(r);
		this.setPoint(norm);

		this.add(this.coneMesh, this.cylinMesh);
	}
	#setRadius(r) {
		this.cylinMesh.scale.set(r, this.cylinMesh.scale.y, r);
		this.coneMesh.scale.set(r*(1+this.rFrac), this.coneMesh.scale.y, r*(1+this.rFrac));
	}
	setPoint(point, scale = 1) {
		this.point = point
		this.quaternion.setFromUnitVectors(this.yHat, point.clone().normalize());
		this.setScale(scale);
	}
	setScale(scale) {
		this.length = this.point.length()*scale;
		this.coneMesh.scale.y = Math.min(this.length*this.frac, this.coneMaxScale);
		this.cylinMesh.scale.y = this.length - this.coneMesh.scale.y;
		this.coneMesh.position.setY(this.cylinMesh.scale.y + this.coneMesh.scale.y/2);
		this.cylinMesh.position.setY(this.cylinMesh.scale.y/2, 0);
		this.#setRadius(Math.min(this.length*this.r, this.r));
	}
	dispose() {
		this.parent?.remove(this);
		this.mat.dispose();
		this.coneGeom.dispose();
		this.cylinGeom.dispose();
	}
}