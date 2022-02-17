#!/usr/bin/env python3
##############################################################################
# EVOLIFE  http://evolife.telecom-paris.fr             Jean-Louis Dessalles  #
# Telecom Paris  2021                                      www.dessalles.fr  #
# -------------------------------------------------------------------------- #
# License:  Creative Commons BY-NC-SA                                        #
##############################################################################

##############################################################################
# Draw curves offline using matplotlib                                       #
##############################################################################

""" Draw curves offline.
	Takes a csv file as input and draws curves.
	Creates image file.
"""


import sys
import os
import re
import glob
import numpy as np
import matplotlib
matplotlib.use('Agg')	# to use offline
import matplotlib.pyplot as plt


import logging	# for tracing
# modifying print priority of console handler
logging.basicConfig(level='WARNING')

sys.path.append('..')
sys.path.append('../..')
sys.path.append('../../..')
sys.path.append('../../../..')
import Evolife.Scenarii.Parameters as EP


try:	import TableCsv as CSV
except ImportError:	import Evolife.Tools.TableCsv as CSV


def figsave(FileName):
	if os.path.exists(FileName):	os.remove(FileName)
	plt.savefig(FileName)
	print("%s created" % FileName)

def str2nb(x):	
	try: return int(x)
	except ValueError:	return float(x)
	
	
	
"""
	
plt.plot(*zip(*Maxima), c='k', linewidth=1, marker='o')	
	

plt.clf()
plt.scatter(alphaValues, [p[1] for p in Prices], color=colours, s=44)
plt.plot(alphaValues, [p[1] for p in Prices], 'r', label='Signal prices')
plt.scatter(alphaValues, [thetaU(a, UC) for a in alphaValues], color=colours, s=44)

"""

class Plot:
	def __init__(self, ExpeFile, FieldDraw=True, ConstantConfigFileName=None):	
		self.ExpeFile = os.path.splitext(ExpeFile)[0]
		if self.ExpeFile.endswith('_res'):	
			self.ExpeFile = self.ExpeFile[:-4]
			SkipFile =  True	# not a data file
		OutputFile = self.ExpeFile + '.png'
		if not os.path.exists(OutputFile):
			self.Dirname, self.ExpeName = os.path.split(self.ExpeFile)
			PlotFile = self.ExpeFile + '.csv'
			self.ConfigFileName = self.ExpeFile + '_res.csv'
			self.Cfg = self.RetrieveConfig(self.ConfigFileName)	# retrieve actual parameters from _res file
			self.RelevantParam = self.RelevantConfig(self.ExpeName, ConstantConfigFileName)	# display parameters 
			# drawing curves
			plt.figure(1, figsize=(6 + 6 * FieldDraw, 4))
			if FieldDraw:	plt.subplot(1,2,1)
			ymax = self.Draw_Curve(PlotFile)
			if self.RelevantParam:	plt.title('   '.join(sorted(['%s = %s' % (P, self.RelevantParam[P]) for P in self.RelevantParam])))
			if FieldDraw:	
				# drawing field
				plt.subplot(1,2,2)
				# self.Draw_Field(self.ExpeFile + '_dmp.csv', ymax=ymax)
				self.Draw_Field(self.ExpeFile + '_dmp.csv', ymax=100)
				plt.title(self.ExpeFile)
			self.save(OutputFile)
		else:	print('%s already exists' % OutputFile)
			
		
	def Draw_Curve(self, CurveFileName):
		# colours = ['#000000', '#00BF00', '#78FF78', '#BF0000', '#FF7878', '#0000BF', '#7878FF']
		colours = ['#00BF00', '#78FF78', '#BF0000', '#FF7878', '#0000BF', '#7878FF']
		# Retrieving coordinates
		PlotOrders = CSV.load(CurveFileName, sniff=True)	# loading csv file
		# Retrieving legend
		try:	Legend = next(PlotOrders)		# reading first line with curve names
		except StopIteration:	sys.exit(0)
		# Retrieving data
		Data = list(zip(*PlotOrders))
		Data = list(map(lambda L: list(map(str2nb, L)), Data))
		# Data = list(map(lambda L: list(map(str2nb, L)), [*PlotOrders]))
		for Col in range(1,len(Data)):
			plt.plot(Data[0], Data[Col], linewidth=2, color=colours[Col-1], label=Legend[Col])	
		x1,x2,y1,y2 = plt.axis()
		plt.axis((x1, x2, 0, y2+0.05))
		# plt.ylim(top=100)
		plt.xlabel('year')
		# plt.ylabel('price or sales')
		# plt.legend(bbox_to_anchor=(0.1, 1))
		plt.legend(loc='upper right')
		return plt.ylim()[1]	# max coordinate
		
	@classmethod
	def RetrieveConfig(self, ConfigFile):
		" Retrieves parameters from _res file "
		if os.path.exists(ConfigFile):
			CfgLines = open(ConfigFile).readlines()
			# reading parameters
			Sep = max([';', '\t', ','], key=lambda x: CfgLines[0].count(x))
			if len(CfgLines) > 1:
				Parameters = dict(zip(*map(lambda x: x.strip().split(Sep), CfgLines[:2])))
				return EP.Parameters(ParamDict=Parameters)
		return None
		
	def RelevantConfig(self, ExpeName, ConstantParameterFile):
		" Try to find relevant parameters "
		Irrelevant =  ['BatchMode', 'DisplayPeriod', 'TimeLimit', 'DumpStart']
		if self.Cfg is None or not ConstantParameterFile:	
			print('ConfigFile not found')
			return None
		RelevantParameters = {}
		CP = EP.Parameters(ConstantParameterFile)
		# determining relevant parameters
		for p in CP:
			if p in Irrelevant:	continue
			if p in self.Cfg and CP[p] != self.Cfg[p]:
				# print(p, RelevantParameters[p], self.Cfg[p])
				RelevantParameters[p] = self.Cfg[p]
				# CP.addParameter(p, self.Cfg[p])
		RelevantParameters = EP.Parameters(ParamDict=RelevantParameters)
		print(RelevantParameters)
		return RelevantParameters
		
	def Draw_Field(self, DumpFile, ymax=None):
		if not os.path.exists(DumpFile):	return None
		Lines = open(DumpFile).readlines()
		# reading recorded positions
		FieldPlot = None
		if len(Lines) > 1:
			FieldPlot = Lines[1].strip().split(';')[1:]
			NbP = len(FieldPlot)
			plt.scatter(list(range(NbP)), list(map(float, FieldPlot)), s=11)
			# print(FieldPlot)
			if ymax is not None:
				plt.ylim(top=ymax)
			plt.xlabel('quality')
			plt.ylabel('signal')
		return FieldPlot
		
	def save(self, OutputFile): figsave(OutputFile)

def Parse(Args):
	Files = []
	ConstantConfigFileName = None
	if len(Args) < 2:
		# find last file
		CsvFiles = glob.glob('___Results/*.csv')
		if CsvFiles:
			CsvFiles.sort(key=lambda x: os.stat(x).st_mtime)
			Files = [CsvFiles[-1]]
	elif len(Args) > 3:
		print('''Usage:	%s <curve file name> [<constant config file name>]''' % os.path.basename(Args[0]))
	else:
		Files = glob.glob(Args[1])
		ConstantConfigFileName = Args[2] if (len(Args) == 3) else None
	for Argfile in Files:
		yield (Argfile, ConstantConfigFileName)
	
if __name__ == "__main__":
	for (Argfile, ConstantConfigFileName) in Parse(sys.argv):
		if Argfile:
			print(Argfile)
			plot = Plot(Argfile, FieldDraw=True, ConstantConfigFileName=ConstantConfigFileName)
			# print()

__author__ = 'Dessalles'
