import * as THREE from 'three'

function makeAxes(scale) {
	const axes = new THREE.AxesHelper(scale);
	axes.setColors('red','green','blue');
	return axes
}

export class Axes extends THREE.Group {
	constructor(scale = 1) {
		super();
		this.scale.set(scale, scale, scale);
		this.xHat = new Arrow(new THREE.Vector3(1,0,0));
		this.yHat = new Arrow(new THREE.Vector3(0,1,0));
		this.zHat = new Arrow(new THREE.Vector3(0,0,1));
		this.add(this.xHat);
		this.add(this.yHat);
		this.add(this.zHat);
		this.setColor('red','lime','blue');
	}
	setColor(xCol, yCol, zCol) {
		this.xHat.mat.color.set(xCol);
		this.yHat.mat.color.set(yCol);
		this.zHat.mat.color.set(zCol);
	}
	setXHat(norm) {
		this.lookAt(new THREE.Vector3().addVectors(this.position, norm));
		this.rotateY(-Math.PI/2);
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

		this.frac = frac;
		this.rFrac = rFrac;
		this.setRadius(r);
		this.setNorm(norm);

		this.add(this.coneMesh);
		this.add(this.cylinMesh);
	}
	setRadius(r) {
		this.cylinMesh.scale.set(r, 1, r);
		this.coneMesh.scale.set(r*(1+this.rFrac), this.frac, r*(1+this.rFrac));
	}
	setNorm(norm) {
		this.length = norm.length();
		this.coneMesh.scale.y = this.length*this.frac;
		this.cylinMesh.scale.y = this.length*(1 - this.frac);
		this.coneMesh.position.setY(this.cylinMesh.scale.y + this.coneMesh.scale.y/2);
		this.cylinMesh.position.setY(this.cylinMesh.scale.y/2, 0);
		this.lookAt(new THREE.Vector3().addVectors(this.position, norm));
		this.rotateX(Math.PI/2);
	}
	dispose() {
		this.parent?.remove(this);
		this.mat.dispose();
		this.coneGeom.dispose();
		this.cylinGeom.dispose();
	}
}