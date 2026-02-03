import numpy as np
import numpy.linalg as LA
from vpython import *

xHat = np.array([1, 0, 0])
yHat = np.array([0, 1, 0])
zHat = np.array([0, 0, 1])

projYZ = np.array([[0, 0, 0],
				   [0, 1, 0],
				   [0, 0, 1]])
projFlipY = np.identity(3)
projFlipY[1][1] = -1

def arr2vec(arr):
	return vec(*arr)
def arr2vert(arr):
	vert = vertex(pos=arr2vec(arr))
	vert.pos_orig = arr
	return vert
def vec2arr(vec):
	return np.array([vec.x, vec.y, vec.z])

def unit(arr):
    return arr/LA.norm(arr)