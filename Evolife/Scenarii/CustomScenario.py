#!/usr/bin/env python3
##############################################################################
# EVOLIFE  http://evolife.telecom-paris.fr             Jean-Louis Dessalles  #
# Telecom Paris  2021                                      www.dessalles.fr  #
# -------------------------------------------------------------------------- #
# License:  Creative Commons BY-NC-SA                                        #
##############################################################################


""" Customized scenario.
	Use this if you REALLY need to re-implement the 
	- Individual
	- Group
	- Observer
	classes. Otherwise, create a scenation named S_xxx.py
	as shown in the many examples contained in this directory.
"""



import sys
sys.path.append('../..')

import Evolife.Tools.Tools as ET
import Evolife.Ecology.Observer as EO
import Evolife.Ecology.Individual as EI
import Evolife.Ecology.Group as EG
import Evolife.Ecology.Population as EP
import Evolife.Ecology.Alliances as EA
import Evolife.Scenarii.Default_Scenario as EDS
import Evolife.QtGraphics.Evolife_Window as EW

class Scenario(EDS.Default_Scenario):
	""" Implement a scenario here, by instantiating Default_Scenario.
		See documentation in Default_Scenario.py to see how.
	"""
	
	def __init__(self):
		EDS.Default_Scenario.__init__(self, Name='MyCustomScenario') # loads 'MyCustomScenario.evo'
		
	def genemap(self):
		return [('gene1',16),('gene2',4)]
	
	def display_(self):
		return [('blue', 'gene1', 'First gene'), ('green4', 'gene2', 'Second gene')]
		
		
class Observer(EO.EvolifeObserver):
	"""	Observer stores display instructions and makes statistics
		See Evolife/Other/GraphicExample.py for examples
	"""
	def Field_grid(self):
		" initial draw: here a blue line "
		return [(0, 0, 'blue', 1, 100, 100, 'blue', 1), (100, 100, 1, 0)]
		
class Individual(EI.EvolifeIndividual):
	"   class Individual: defines what an individual consists of "

	def __init__(self, Scenario=None, ID=None, Newborn=False, maxQuality=100):
		EI.EvolifeIndividual.__init__(self, Scenario=Scenario, ID=ID, Newborn=Newborn)
		self.Quality = (100.0 * int(ID)) / maxQuality # quality may be displayed
		self.Points = 0	# stores current performance
		self.Risk = 0	# Risk taking
	
	
class Group(EG.EvolifeGroup):
	" Calls local class when creating individuals "
	
	def createIndividual(self, ID=None, Newborn=True):
		return Individual(self.Scenario, ID=self.free_ID(Prefix=''), Newborn=Newborn)


class Population(EP.EvolifePopulation):
	" Calls local class when creating group "

	def createGroup(self, ID=0, Size=0):
		return Group(self.Scenario, ID=ID, Size=Size)

	def season_initialization(self):
		for gr in self.groups:
			for agent in gr:
				# agent.lessening_friendship()	# eroding past gurus performances
				if self.Scenario['EraseNetwork']:	agent.forgetAll()
				agent.Points = 0
				agent.Risk = 100	# maximum risk
		
	
if __name__ == "__main__":
	Gbl = Scenario()	# includes parameters
	Obs = Observer(Gbl)	
	Pop = Population(Scenario=Gbl, Evolife_Obs=Obs)
	if Gbl['BatchMode'] == 0:	print(__doc__)
	
	# launching windows
	# See Evolife_Window.py for details
	Capabilities='FGCP'	# F = 'Field'; G = 'Genomes'; C = 'Curves'; 
	Views = []
	if 'F' in Capabilities:	Views.append(('Field', 500, 350))	# start with 'Field' window on screen
	if 'T' in Capabilities:	Views.append(('Trajectories', 500, 350))	# 'Trajectories' on screen
	Obs.recordInfo('DefaultViews',	Views)	# Evolife should start with these window open
	EW.Start(SimulationStep=Pop.one_year, Obs=Obs, Capabilities=Capabilities, 
		Options=[('Background','green11')])
	


__author__ = 'Dessalles'
