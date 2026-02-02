from vpython import *
import numpy as np

from import_stl import *
from model_constants import *
from model_6DoF import *
from utils import *
from panel import *

theta_cam = np.deg2rad(-45)
phi_cam = np.deg2rad(30 + 90)

scene = canvas(title='Axis Dev', width=1200, height=700, resizable=True)
scene.up = vec(0,0,-1)
scene.lights = []
top_light = distant_light(direction=vec(0.22,-0.44,-0.88),color=color.white*0.8)
bottom_light = distant_light(direction=vec(-0.22,0.44,0.88),color=color.white*0.3)
scene.forward = vec(-cos(theta_cam)*sin(phi_cam), -sin(theta_cam)*sin(phi_cam), -cos(phi_cam))

geometry_path = r"D:\Secondary Storage\PEP 26\Reverse Engineering\E1 Racebird\geometry\body frame aligned"
vec_CM = arr2vec(r_CM)
vecZero = arr2vec(np.zeros(3))
hull = stl_compound(geometry_path+r"\RBird_Hull_Remesh.stl", vec_CM)
wing = stl_compound(geometry_path+r"\Wing_Applied_Low_Poly.stl", vec_CM)
rear_wing = stl_compound(geometry_path+r"\Rear_Wing_Applied_Low_Poly.stl", vec_CM)
model = compound([hull, wing, rear_wing])
model.pos = vecZero
def model_toggle():
	model.visible = not model.visible
model_button = button(text='Model', bind=model_toggle)

waterplane = box(size=vec(10,10,0.01), color=color.blue, opacity=0.3)
def waterplane_toggle():
	waterplane.visible = not waterplane.visible
waterplane_button = button(text='Waterplane', bind=waterplane_toggle)

panel_v_L = Panel([r_LE_vr, r_TE_vr, r_LE_v1, r_TE_v1], r_CM, -1)
panel_1_L = Panel([r_LE_v1, r_TE_v1, r_LE_12, r_TE_12], r_CM)
panel_2_L = Panel([r_LE_12, r_TE_12, r_LE_23, r_TE_23], r_CM)
panel_3_L = Panel([r_LE_23, r_TE_23, r_LE_3t, r_TE_3t], r_CM)

panel_r1_L = Panel([r_LE_r1t, r_TE_r1t, r_LE_r12, r_TE_r12], r_CM)
panel_r2_L = Panel([r_LE_r12, r_TE_r12, r_LE_r2m, r_TE_r2m], r_CM)
panel_rv_L = Panel([r_LE_rvs, r_TE_rvs, r_LE_r12v, r_TE_r12v], r_CM, -1)
panel_rs_L = Panel([r_LE_rsr, r_TE_rsr, r_LE_rvs, r_TE_rvs], r_CM, -1)

panel_v_R = Panel([projFlipY @ v for v in [r_LE_vr, r_TE_vr, r_LE_v1, r_TE_v1]], r_CM)
panel_1_R = Panel([projFlipY @ v for v in [r_LE_v1, r_TE_v1, r_LE_12, r_TE_12]], r_CM, -1)
panel_2_R = Panel([projFlipY @ v for v in [r_LE_12, r_TE_12, r_LE_23, r_TE_23]], r_CM, -1)
panel_3_R = Panel([projFlipY @ v for v in [r_LE_23, r_TE_23, r_LE_3t, r_TE_3t]], r_CM, -1)

panel_r1_R = Panel([projFlipY @ v for v in [r_LE_r1t, r_TE_r1t, r_LE_r12, r_TE_r12]], r_CM, -1)
panel_r2_R = Panel([projFlipY @ v for v in [r_LE_r12, r_TE_r12, r_LE_r2m, r_TE_r2m]], r_CM, -1)
panel_rv_R = Panel([projFlipY @ v for v in [r_LE_rvs, r_TE_rvs, r_LE_r12v, r_TE_r12v]], r_CM)
panel_rs_R = Panel([projFlipY @ v for v in [r_LE_rsr, r_TE_rsr, r_LE_rvs, r_TE_rvs]], r_CM)

panels = [panel_v_L, panel_1_L, panel_2_L, panel_3_L, panel_r1_L, panel_r2_L, panel_rv_L, panel_rs_L,
		  panel_v_R, panel_1_R, panel_2_R, panel_3_R, panel_r1_R, panel_r2_R, panel_rv_R, panel_rs_R]
def panels_toggle():
	for panel in panels:
		panel.toggle_panel()
		panel.toggle_panel_subm()
panels_button = button(text='Panels', bind=panels_toggle)
def panel_normals_toggle():
	for panel in panels:
		panel.toggle_normal()
normals_button = button(text='Normals', bind=panel_normals_toggle)
def foil_frame_toggle():
	for panel in panels:
		panel.toggle_foil_frame()
foil_frame_button = button(text='Foil Frame', bind=foil_frame_toggle)
def water_frame_toggle():
	for panel in panels:
		panel.toggle_water_frame()
water_frame_button = button(text='Water Frame', bind=water_frame_toggle)

def update_panels(C0b):
	for panel in panels:
		panel.update_panel(C0b, r_0)
def update_panel_frames(C0b, vel=None, omega=None):
	if vel is None:
		vel = np.array([u, v, w])
	if omega is None:
		omega = np.array([p, q, r])
	for panel in panels:
		panel.update_frames(C0b, vel, omega)

body_frame = [arrow(axis=vec(*xHat),color=color.red,round=True),
			  arrow(axis=vec(*yHat),color=color.green,round=True),
			  arrow(axis=vec(*zHat),color=color.blue,round=True)]
def body_frame_toggle():
	for arr in body_frame:
		arr.visible = not arr.visible
body_frame_button = button(text='Body Frame', bind=body_frame_toggle)

fixed_frame = [arrow(axis=vec(*xHat),color=color.red,round=True),
			  arrow(axis=vec(*yHat),color=color.green,round=True),
			  arrow(axis=vec(*zHat),color=color.blue,round=True)]
def fixed_frame_toggle():
	for arr in fixed_frame:
		arr.visible = not arr.visible
fixed_frame_button = button(text='Fixed Frame', bind=fixed_frame_toggle)

prop_frame = [arrow(axis=vec(*xHat)*0.1,color=color.red,round=True),
			  arrow(axis=vec(*yHat)*0.1,color=color.green,round=True),
			  arrow(axis=vec(*zHat)*0.1,color=color.blue,round=True)]
def prop_frame_toggle():
	for arr in prop_frame:
		arr.visible = not arr.visible
prop_frame_button = button(text='Prop Frame', bind=prop_frame_toggle)

def update_prop_frame(C0b, r0=None, theta_p=None, psi_p=None):
	if theta_p is None or psi_p is None:
		theta_p = theta_prop
		psi_p = psi_prop
	else:
		global Cpb, Cbp
		Cpb = np.array([
			[cos(theta_p)*cos(psi_p), sin(psi_p), -sin(theta_p)*cos(psi_p)],
			[-cos(theta_p)*sin(psi_p), cos(psi_p), sin(theta_p)*sin(psi_p)],
			[sin(theta_p), 0, cos(theta_p)]
		])
		Cbp = np.transpose(Cpb)
	if r0 is None:
		r0 = r_0
	C0p = C0b @ Cbp
	prop_frame[0].axis = arr2vec(C0p @ xHat) * 0.1
	prop_frame[1].axis = arr2vec(C0p @ yHat) * 0.1
	prop_frame[2].axis = arr2vec(C0p @ zHat) * 0.1

	for arr in prop_frame:
		arr.pos = arr2vec(C0b @ (r_prop - r_CM) + r0)

locations = []
for name, value in locals().copy().items():
	if isinstance(value, np.ndarray) and name.startswith('r_'):
		lbl = label(pos=vec(*(value - r_CM)), text=name, space=0.05)
		lbl.pos_orig = value - r_CM
		locations.append(lbl)
def locations_toggle():
	for loc in locations:
		loc.visible = not loc.visible
locations_button = button(text='Locations', bind=locations_toggle)

def update_locations(C0b):
	for loc in locations:
		loc.pos = arr2vec(C0b @ loc.pos_orig + r_0)

def model_rotation():
	global C0b
	phi = np.deg2rad(phi_slider.value)
	theta = np.deg2rad(theta_slider.value)
	psi = np.deg2rad(psi_slider.value)
	C0b = update_C0b(phi, theta, psi)
	model.axis = arr2vec(C0b @ xHat)
	model.up = arr2vec(C0b @ yHat)

	body_frame[0].axis = arr2vec(C0b @ xHat)
	body_frame[1].axis = arr2vec(C0b @ yHat)
	body_frame[2].axis = arr2vec(C0b @ zHat)

	phi_text.text = f'ϕ: {phi_slider.value:.1f}°'
	theta_text.text = f'θ: {theta_slider.value:.1f}°'
	psi_text.text = f'ψ: {psi_slider.value:.1f}°'

	update_panels(C0b)
	update_panel_frames(C0b)
	update_locations(C0b)
	update_prop_frame(C0b)

scene.append_to_caption('\n')
phi_slider = slider(bind=model_rotation, min=-24, max=24, value=np.rad2deg(phi))
phi_text = wtext(text=f'ϕ: {phi_slider.value:.1f}°')
theta_slider = slider(bind=model_rotation, min=-12, max=12, value=np.rad2deg(theta))
theta_text = wtext(text=f'θ: {theta_slider.value:.1f}°')
psi_slider = slider(bind=model_rotation, min=0, max=360, value=np.rad2deg(psi))
psi_text = wtext(text=f'ψ: {psi_slider.value:.1f}°')

def model_position():
	global r_0
	r_0[0] = x0_slider.value
	r_0[1] = y0_slider.value
	r_0[2] = z0_slider.value
	model.pos = arr2vec(r_0)
	for arr in body_frame:
		arr.pos = model.pos

	x0_text.text = f'x0: {r_0[0]:.2f} m'
	y0_text.text = f'y0: {r_0[1]:.2f} m'
	z0_text.text = f'z0: {r_0[2]:.2f} m'

	update_panels(C0b)
	update_panel_frames(C0b)
	update_locations(C0b)
	update_prop_frame(C0b, r_0)

scene.append_to_caption('\n')
x0_slider = slider(bind=model_position, min=-1, max=1, value=r_0[0])
x0_text = wtext(text=f'x0: {r_0[0]:.2f} m')
y0_slider = slider(bind=model_position, min=-1, max=1, value=r_0[1])
y0_text = wtext(text=f'y0: {r_0[1]:.2f} m')
z0_slider = slider(bind=model_position, min=-1, max=1, value=r_0[2])
z0_text = wtext(text=f'z0: {r_0[2]:.2f} m')

def model_rate():
	global u, v, w, p, q, r
	u = u_slider.value
	v = v_slider.value
	w = w_slider.value

	p = np.deg2rad(p_slider.value)
	q = np.deg2rad(q_slider.value)
	r = np.deg2rad(r_slider.value)

	u_text.text=f'u: {u:.1f} m/s'
	v_text.text=f'v: {v:.1f} m/s'
	w_text.text=f'w: {w:.1f} m/s'

	p_text.text=f'p: {p_slider.value:.1f}°/s'
	q_text.text=f'q: {q_slider.value:.1f}°/s'
	r_text.text=f'r: {r_slider.value:.1f}°/s'

	update_panel_frames(C0b, np.array([u, v, w]), np.array([p, q, r]))

scene.append_to_caption('\n')
u_slider = slider(bind=model_rate, min=0, max=15, value=u)
u_text = wtext(text=f'u: {u_slider.value:.1f} m/s')
v_slider = slider(bind=model_rate, min=0, max=5, value=v)
v_text = wtext(text=f'v: {v_slider.value:.1f} m/s')
w_slider = slider(bind=model_rate, min=0, max=5, value=w)
w_text = wtext(text=f'w: {w_slider.value:.1f} m/s')

scene.append_to_caption('\n')
p_slider = slider(bind=model_rate, min=-360, max=360, value=np.rad2deg(p))
p_text = wtext(text=f'p: {p_slider.value:.1f}°/s')
q_slider = slider(bind=model_rate, min=-360, max=360, value=np.rad2deg(q))
q_text = wtext(text=f'q: {q_slider.value:.1f}°/s')
r_slider = slider(bind=model_rate, min=-180, max=180, value=np.rad2deg(r))
r_text = wtext(text=f'r: {r_slider.value:.1f}°/s')

def prop_angle():
	global theta_prop, psi_prop
	theta_prop = np.deg2rad(theta_p_slider.value)
	psi_prop = np.deg2rad(psi_p_slider.value)

	theta_p_text.text = f'θp: {theta_p_slider.value:.1f}°'
	psi_p_text.text = f'ψp: {psi_p_slider.value:.1f}°'

	update_prop_frame(C0b, r_0, theta_prop, psi_prop)

scene.append_to_caption('\n')
theta_p_slider = slider(bind=prop_angle, min=-10, max=10, value=np.rad2deg(theta_prop))
theta_p_text = wtext(text=f'θp: {theta_p_slider.value:.1f}°')
psi_p_slider = slider(bind=prop_angle, min=-30, max=30, value=np.rad2deg(psi_prop))
psi_p_text = wtext(text=f'ψp: {psi_p_slider.value:.1f}°')

update_panels(C0b)
update_panel_frames(C0b)
update_prop_frame(C0b)

while True:
	pass