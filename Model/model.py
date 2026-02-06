import numpy as np
import numpy.linalg as la

class Model_6DoF:
	def __init__(self, path_constants, path_hull):
		self.constants = {}
		warnings = 0
		# load model constants
		with open(path_constants,'r') as file:
			for line in file:
				# comment
				if line.startswith('#') or line.isspace():
					continue
				sep = line.find('=')
				key = line[:sep].strip()
				valueStr = line[sep+1:line.find('#')].strip()
				# blank
				if len(valueStr) == 0 or valueStr.isspace():
					print(f'WARNING: blank entry for key: {key}')
					warnings += 1
					continue
				# vector
				if valueStr.startswith('('):
					value = []
					for v in valueStr[1:-1].split(','):
						try:
							value.append(float(v))
						except:
							print(f'WARNING: nonfloat component for vector: {key}')
							warnings += 1
							continue
					if len(value) != 3:
						continue
					if not key.startswith('r_'): key = 'r_' + key
				# scalar
				else:
					try:
						value = float(valueStr)
					except:
						print(f"WARNING: nonfloat value for key: {key}")
						warnings += 1
						continue
				self.constants[key] = value
				# print(f'key: {f"{key}":<12}\tvalue: {value}')
		# load hull parameters
		with open(path_hull, 'r') as file:
			pass
		
		if warnings > 0:
			print(f'Loaded model constants with {warnings} warnings, continue? (1-yes, 0-no): ')
			str = input()
			confirms = ['1', 'y', 'yes']
			if str not in confirms:
				exit()

			

Model_6DoF('model_constants.txt')