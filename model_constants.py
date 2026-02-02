import numpy as np
from vpython import *

from utils import *

# All values defined for Left Wing
# --- Point Locations (m) ---
# Format: [X (front), Y (right), Z (down)]
r_CM = np.array([32, 0, -12]) / 100
r_prop = np.array([-19, 0, 13.6]) / 100

r_LE_vr  = np.array([67.695, -46.642, -16.876]) / 100
r_TE_vr  = np.array([37.695, -46.642, -16.876]) / 100

r_LE_v1  = np.array([67.695, -47.642, 0.0]) / 100
r_TE_v1  = np.array([42.695, -47.642, 0.0]) / 100

r_LE_12  = np.array([71.395, -25.642, 12.124]) / 100
r_TE_12  = np.array([61.695, -25.642, 12.124]) / 100

r_LE_23  = np.array([71.395, -14.042, 14.824]) / 100
r_TE_23  = np.array([66.695, -14.042, 14.824]) / 100

r_LE_3t  = np.array([68.695, -14.042, 18.824]) / 100
r_TE_3t  = np.array([66.695, -14.042, 18.824]) / 100

# -- Rear Wing --

r_LE_r1t = np.array([-17.808, -25.642, 22.124]) / 100
r_TE_r1t = np.array([-21.905, -25.642, 22.124]) / 100

r_LE_r12 = np.array([-6.3054, -8.6424, 22.124]) / 100
r_TE_r12 = np.array([-17.305, -8.6424, 22.124]) / 100

r_LE_r2m = np.array([-6.3054, 0.0, 22.124]) / 100
r_TE_r2m = np.array([-17.305, 0.0, 22.124]) / 100

r_LE_r12v = np.array([-11.305, -8.6424, 22.124]) / 100
r_TE_r12v = np.array([-17.305, -8.6424, 22.124]) / 100

r_LE_rvs  = np.array([-11.305, -8.6424, 7.1239]) / 100
r_TE_rvs  = np.array([-17.305, -8.6424, 7.1239]) / 100

r_LE_rsr  = np.array([-11.305, -3.1211, 0.0]) / 100
r_TE_rsr  = np.array([-17.305, -3.1211, 0.0]) / 100

# --- Quarter Chord Locations (m) ---
r_qc_vr = 3/4*r_LE_vr + 1/4*r_TE_vr
r_qc_v1 = 3/4*r_LE_v1 + 1/4*r_TE_v1
r_qc_12 = 3/4*r_LE_12 + 1/4*r_TE_12
r_qc_23 = 3/4*r_LE_23 + 1/4*r_TE_23
r_qc_3t = 3/4*r_LE_3t + 1/4*r_TE_3t

r_qc_r1t = 3/4*r_LE_r1t + 1/4*r_TE_r1t
r_qc_r12 = 3/4*r_LE_r12 + 1/4*r_TE_r12
r_qc_r2m = 3/4*r_LE_r2m + 1/4*r_TE_r2m
r_qc_r12v = 3/4*r_LE_r12v + 1/4*r_TE_r12v
r_qc_rvs = 3/4*r_LE_rvs + 1/4*r_TE_rvs
r_qc_rsr = 3/4*r_LE_rsr + 1/4*r_TE_rsr

# --- Chord Lengths (m) ---
cvr = np.linalg.norm(r_LE_vr - r_TE_vr)
cv1 = np.linalg.norm(r_LE_v1 - r_TE_v1)
c12 = np.linalg.norm(r_LE_12 - r_TE_12)
c23 = np.linalg.norm(r_LE_23 - r_TE_23)
c3t = np.linalg.norm(r_LE_3t - r_TE_3t)

cr1t = np.linalg.norm(r_LE_r1t - r_TE_r1t)
cr12 = np.linalg.norm(r_LE_r12 - r_TE_r12)
cr2m = np.linalg.norm(r_LE_r2m - r_TE_r2m)
cr12v = np.linalg.norm(r_LE_r12v - r_TE_r12v)
crvs = np.linalg.norm(r_LE_rvs - r_TE_rvs)
crsr = np.linalg.norm(r_LE_rsr - r_TE_rsr)

# --- Span Lengths (m) ---
sv = np.linalg.norm(projYZ @ (r_LE_vr - r_LE_v1))
s1 = np.linalg.norm(projYZ @ (r_LE_v1 - r_LE_12))
s2 = np.linalg.norm(projYZ @ (r_LE_12 - r_LE_23))
s3 = np.linalg.norm(projYZ @ (r_LE_23 - r_LE_3t))

sr1 = np.linalg.norm(projYZ @ (r_LE_r1t - r_LE_r12))
sr2 = np.linalg.norm(projYZ @ (r_LE_r12 - r_LE_r2m))
srv = np.linalg.norm(projYZ @ (r_LE_rvs - r_LE_r12v))
srs = np.linalg.norm(projYZ @ (r_LE_rsr - r_LE_rvs))

# --- Angles (rad) ---
gammav = np.arccos(unit(projYZ @ (r_LE_vr - r_LE_v1)) @ -yHat) - np.pi
gamma1 = np.arccos(unit(projYZ @ (r_LE_v1 - r_LE_12)) @ -yHat)
gamma2 = np.arccos(unit(projYZ @ (r_LE_12 - r_LE_23)) @ -yHat)
gamma3 = np.arccos(unit(projYZ @ (r_LE_23 - r_LE_3t)) @ -yHat)

gammar1 = np.arccos(unit(projYZ @ (r_LE_r1t - r_LE_r12)) @ -yHat)
gammar2 = np.arccos(unit(projYZ @ (r_LE_r12 - r_LE_r2m)) @ -yHat)
gammarv = np.arccos(unit(projYZ @ (r_LE_rvs - r_LE_r12v)) @ -yHat) - np.pi
gammars = np.arccos(unit(projYZ @ (r_LE_rsr - r_LE_rvs)) @ -yHat) - np.pi

if (__name__ == '__main__'):
	for name, value in locals().copy().items():
		if not name.startswith('__'):
			if 'gamma' in name:
				print(f"{name}: {np.rad2deg(value)}")
			else:
				print(f"{name}: {value}")