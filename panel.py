from vpython import *
import numpy as np
import numpy.linalg as LA
import copy

from utils import *

class Panel:
	def __init__(self, rList, r_CM, norm_mult=1):
		self.r_LE_1 = rList[0]
		self.r_TE_1 = rList[1]
		self.r_LE_2 = rList[2]
		self.r_TE_2 = rList[3]
		self.r_CM = r_CM

		self.r_qc_1 = 3/4*self.r_LE_1 + 1/4*self.r_TE_1
		self.r_qc_2 = 3/4*self.r_LE_2 + 1/4*self.r_TE_2

		self.c1 = LA.norm(self.r_LE_1 - self.r_TE_1)
		self.c2 = LA.norm(self.r_LE_2 - self.r_TE_2)

		self.s = LA.norm(projYZ @ (self.r_LE_1 - self.r_LE_2))

		self.gamma = np.arccos(unit(projYZ @ (self.r_LE_1 - self.r_LE_2)) @ -yHat)
		if self.gamma > pi/2:
			self.gamma -= pi

		self.Cfb = np.array([
			[1, 0, 0],
			[0, cos(self.gamma), sin(self.gamma)],
			[0, -sin(self.gamma), cos(self.gamma)]
		])
		self.Cbf = np.transpose(self.Cfb)

		self.normal = unit(LA.cross(self.r_LE_1 - self.r_LE_2, self.r_TE_2 - self.r_LE_2)) * norm_mult
		verts = [arr2vert(self.r_LE_2 - r_CM), arr2vert(self.r_LE_1 - r_CM), 
		   arr2vert(self.r_TE_1 - r_CM), arr2vert(self.r_TE_2 - r_CM)]
		for vert in verts:
			vert.normal = arr2vec(self.normal)

		self.r_qc_half = (self.r_qc_1 + self.r_qc_2)/2
		vCenter = arr2vec(self.r_qc_half - r_CM)

		self.arrow = arrow(pos=vCenter, axis=arr2vec(self.normal) * 0.1, color=color.orange)
		verts_subm = [vertex(pos=vert.pos, normal=vert.normal) for vert in verts]
		for vert in verts_subm:
			vert.color = self.arrow.color
		
		self.panel = quad(vs=verts)
		self.panel_subm = quad(vs=verts_subm)

		self.foil_frame = [
			arrow(pos=vCenter, axis = arr2vec(xHat) * 0.1, color=color.red, round=True),
			arrow(pos=vCenter, axis = arr2vec(yHat) * 0.1, color=color.green, round=True),
			arrow(pos=vCenter, axis = arr2vec(zHat) * 0.1, color=color.blue, round=True)
		]

		self.water_frame = [
			arrow(pos=vCenter, axis = arr2vec(xHat) * 0.1, color=color.red, round=True),
			arrow(pos=vCenter, axis = arr2vec(yHat) * 0.1, color=color.green, round=True),
			arrow(pos=vCenter, axis = arr2vec(zHat) * 0.1, color=color.blue, round=True)
		]

	def update_panel(self, C0b, r_0):
		# submergence
		swap = (C0b @ self.r_qc_1)[2] > (C0b @ self.r_qc_2)[2]
		if swap:
			r_qc_1 = self.r_qc_2
			r_qc_2 = self.r_qc_1
			c1 = self.c2
			c2 = self.c1
		else:
			r_qc_1 = self.r_qc_1
			r_qc_2 = self.r_qc_2
			c1 = self.c1
			c2 = self.c2
		if (C0b @ (r_qc_2 - r_qc_1))[2] <= 1e-6:
			self.f = 1 if (C0b @ (r_qc_2 - self.r_CM) + r_0)[2] > 0 else 0
		else:
			self.f = (C0b @ (r_qc_2 - self.r_CM) + r_0)[2] / (C0b @ (r_qc_2 - r_qc_1))[2]
			self.f = np.max([np.min([self.f, 1]), 0])
		cf = c2 + (c1-c2)*self.f
		self.A = 1/2*(c1+cf)*self.s*self.f
		sC = self.s*self.f/3*(c2 + 2*cf)/(c2 + cf)
		fC = sC/self.s
		self.r_qc_fC = r_qc_2 + (r_qc_1 - r_qc_2)*fC
		
		vNorm = arr2vec(C0b @ self.normal)

		self.arrow.pos = arr2vec(C0b @ (self.r_qc_fC - self.r_CM) + r_0)
		self.arrow.axis = vNorm * 0.1 * self.f

		# panel quad locations
		if swap:
			r_LE_1 = self.r_LE_2
			r_LE_2 = self.r_LE_1
			r_TE_1 = self.r_TE_2
			r_TE_2 = self.r_TE_1
		else:
			r_LE_1 = self.r_LE_1
			r_LE_2 = self.r_LE_2
			r_TE_1 = self.r_TE_1
			r_TE_2 = self.r_TE_2
		r_LE_f = r_LE_2 + (r_LE_1 - r_LE_2)*self.f
		r_TE_f = r_TE_2 + (r_TE_1 - r_TE_2)*self.f

		self.panel.v0.pos = arr2vec(C0b @ (r_LE_f - self.r_CM) + r_0)
		self.panel.v1.pos = arr2vec(C0b @ (r_LE_1 - self.r_CM) + r_0)
		self.panel.v2.pos = arr2vec(C0b @ (r_TE_1 - self.r_CM) + r_0)
		self.panel.v3.pos = arr2vec(C0b @ (r_TE_f - self.r_CM) + r_0)
		
		self.panel_subm.v0.pos = arr2vec(C0b @ (r_LE_2 - self.r_CM) + r_0)
		self.panel_subm.v1.pos = arr2vec(C0b @ (r_LE_f - self.r_CM) + r_0)
		self.panel_subm.v2.pos = arr2vec(C0b @ (r_TE_f - self.r_CM) + r_0)
		self.panel_subm.v3.pos = arr2vec(C0b @ (r_TE_2 - self.r_CM) + r_0)

		for vert in self.panel.vs + self.panel_subm.vs:
			vert.normal = vNorm

		# frame locations
		for arr in self.foil_frame:
			arr.pos = arr2vec(C0b @ (self.r_qc_half - self.r_CM) + r_0)
		for arr in self.water_frame:
			arr.pos = arr2vec(C0b @ (self.r_qc_fC - self.r_CM) + r_0)
	
	def update_frames(self, C0b, vel, rate):
		vel_foil = vel + np.cross(rate, self.r_qc_fC - self.r_CM)
		self.U_foil = LA.norm(vel_foil)

		vel_foil_fFrame = self.Cfb @ vel_foil

		if vel_foil[0] <= 1e-6:
			self.alpha = 0
		else:
			self.alpha = np.arctan(vel_foil_fFrame[2] / vel_foil[0])
		if self.U_foil <= 1e-6:
			self.beta = 0
		else:
			self.beta = np.arcsin(vel_foil_fFrame[1] / self.U_foil)

		self.Cfw = np.array([
			[cos(self.alpha)*cos(self.beta), -cos(self.alpha)*sin(self.beta), -sin(self.alpha)],
			[sin(self.beta), cos(self.beta), 0],
			[sin(self.alpha)*cos(self.beta), -sin(self.alpha)*sin(self.beta), cos(self.alpha)]
		])

		self.C0f = C0b @ self.Cbf

		self.foil_frame[0].axis = arr2vec(self.C0f @ xHat) * 0.1
		self.foil_frame[1].axis = arr2vec(self.C0f @ yHat) * 0.1
		self.foil_frame[2].axis = arr2vec(self.C0f @ zHat) * 0.1

		self.C0w = C0b @ self.Cbf @ self.Cfw

		self.water_frame[0].axis = arr2vec(self.C0w @ xHat) * 0.1 * self.f
		self.water_frame[1].axis = arr2vec(self.C0w @ yHat) * 0.1 * self.f
		self.water_frame[2].axis = arr2vec(self.C0w @ zHat) * 0.1 * self.f

	def toggle_panel(self):
		self.panel.visible = not self.panel.visible

	def toggle_panel_subm(self):
		self.panel_subm.visible = not self.panel_subm.visible

	def toggle_normal(self):
		self.arrow.visible = not self.arrow.visible

	def toggle_foil_frame(self):
		for arr in self.foil_frame:
			arr.visible = not arr.visible

	def toggle_water_frame(self):
		for arr in self.water_frame:
			arr.visible = not arr.visible