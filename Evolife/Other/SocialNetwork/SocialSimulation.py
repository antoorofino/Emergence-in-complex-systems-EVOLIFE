#!/usr/bin/env python3
##############################################################################
# EVOLIFE  http://evolife.telecom-paris.fr             Jean-Louis Dessalles  #
# Telecom Paris  2021                                      www.dessalles.fr  #
# -------------------------------------------------------------------------- #
# License:  Creative Commons BY-NC-SA                                        #
##############################################################################


""" A basic framework to run social simulations
"""


from time import sleep
from random import sample, randint, shuffle

import sys
import os.path
sys.path.append('../../..')	# to include path to Evolife

import Evolife.Scenarii.Parameters as EP
# import Evolife.Scenarii.Parameters 	as EP
import Evolife.Tools.Tools as ET
import Evolife.Ecology.Observer as EO
import Evolife.Ecology.Alliances as EA
import Evolife.Ecology.Learner as EL


class Global(EP.Parameters):
	# Global elements
	def __init__(self, ConfigFile='_Params.evo'):
		# Parameter values
		EP.Parameters.__init__(self, ConfigFile)
		self.Parameters = self	# compatibility
		self.ScenarioName = self['ScenarioName']
		# Definition of interactions
		self.Interactions = None	# to be overloaded

	def Dump_(self, PopDump, ResultFileName, DumpFeatures, ExpeID, Verbose=False):
		""" Saves parameter values, then agents' investment in signalling, then agents' distance to best friend
		"""
		if Verbose:	print("Saving data to %s.*" % ResultFileName)
		SNResultFile = open(ResultFileName + '_dmp.csv', 'w')
		SNResultFile.write('%s\n' % ExpeID)	  
		for Feature in DumpFeatures:
			SNResultFile.write(";".join(PopDump(Feature)))	  
			SNResultFile.write("\n")	  
		SNResultFile.close()
		
	# def Param(self, ParameterName):	return self.Parameters.Parameter(ParameterName)


class Social_Observer(EO.Experiment_Observer):
	" Stores some global observation and display variables "

	def __init__(self, Parameters=None):
		EO.Experiment_Observer.__init__(self, Parameters)
		#additional parameters	  
		self.Alliances = []		# social links, for display
		if self.Parameter('AvgFriendDistance'):	
			self.curve('FriendDistance', Color='yellow', Legend='Avg distance to best friend')
		# self.curve('SignalLevel', 50, Color='yellow', Legend='Avg Signal Level')	
		
	def get_data(self, Slot, Consumption=True):
		if Slot == 'Network':	return self.Alliances			# returns stored links
		return EO.Experiment_Observer.get_data(self, Slot, Consumption=Consumption)

	def hot_phase(self):
		return self.StepId < self.TimeLimit * self.Parameter('LearnHorizon') / 100.0

class Social_Individual(EA.Follower, EL.Learner):
	"   A social individual has friends and can learn "

	def __init__(self, IdNb, features={}, maxQuality=100, parameters=None, SocialSymmetry=True):
		if parameters: 	self.Param = parameters.Param
		else:	self.Param = None	# but this will provoke an error
		self.ID = "A%d" % IdNb	# Identity number
		if SocialSymmetry:
			EA.Follower.__init__(self, self.Param('MaxFriends'), self.Param('MaxFriends'))
		else:
			EA.Follower.__init__(self, self.Param('MaxFriends'), self.Param('MaxFollowers'))
		self.Quality = (100.0 * IdNb) / maxQuality # quality may be displayed
		# Learnable features
		EL.Learner.__init__(self, features, MemorySpan=self.Param('MemorySpan'), AgeMax=self.Param('AgeMax'), 
							Infancy=self.Param('Infancy'), Imitation=self.Param('ImitationStrength'), 
							Speed=self.Param('LearningSpeed'), JumpProbability=self.Param('JumpProbability', 0),
							Conservatism=self.Param('LearningConservatism'), 
							LearningSimilarity=self.Param('LearningSimilarity'), 
							toric=self.Param('Toric'), Start=self.Param('LearningStart', default=-1))
		self.Points = 0	# stores current performance
		self.update()

	def Reset(self, Newborn=True):	
		" called by Learner at initialization and when born again "
		self.forgetAll()	# erase friendships
		EL.Learner.Reset(self, Newborn=Newborn)
		
	def reinit(self):	# called at the beginning of each year 
		# self.lessening_friendship()	# eroding past gurus performances
		if self.Param('EraseNetwork'):	self.forgetAll()
		self.Points = 0

	def update(self, infancy=True):
		"	updates values for display "
		Colour = 'green%d' % int(1 + 10 * (1 - float(self.Age)/(1+self.Param('AgeMax'))))
		if infancy and not self.adult():	Colour = 'red'
		if self.Features:	y = self.Features[self.Features.keys()[0]]
		else:	y = 17
		self.location = (self.Quality, y, Colour, 2)


	def Interact(self, Partner):	
		pass	# to be overloaded
		return True

	def assessment(self):
		" Social benefit from having friends - called by Learning "
		pass		# to be overloaded
		
	def __str__(self):
		return "%s[%s]" % (self.ID, str(self.Features))
		
class Social_Population:
	" defines a population of interacting agents "

	def __init__(self, parameters, NbAgents, Observer, IndividualClass=None, features={}):
		" creates a population of agents "
		if IndividualClass is None:	IndividualClass = Social_Individual
		self.Features = features
		self.Pop = [IndividualClass(IdNb, maxQuality=NbAgents, features=features.keys(), 
					parameters=parameters) for IdNb in range(NbAgents)]
		self.PopSize = NbAgents
		self.Obs = Observer
		self.Param = parameters.Param
		self.NbGroup = parameters.get('NbGroup', 1)	# number of groups
				 
	def positions(self):	return [(A.ID, A.location) for A in self.Pop]

	def neighbours(self, Agent):
		" Returns a list of neighbours for an agent "
		AgentQualityRank = self.Pop.index(Agent)
		return [self.Pop[NBhood] for NBhood in [AgentQualityRank - 1, AgentQualityRank + 1]
				if NBhood >= 0 and NBhood < self.PopSize]
		  
	def SignalAvg(self):
		Avg = 0
		for I in self.Pop:	Avg += I.SignalLevel
		if self.Pop:	Avg /= len(self.Pop)
		return Avg
	
	def FeatureAvg(self, Feature):
		Avg = 0
		for I in self.Pop:	Avg += I.feature(Feature)
		if self.Pop:	Avg /= len(self.Pop)
		return Avg
	
	def FriendDistance(self):	
		FD = []
		for I in self.Pop:	
			BF = I.best_friend()
			if BF:	FD.append(abs(I.Quality - BF.Quality))
		if FD:	return sum(FD) / len(FD)
		return 0
		
	def display(self):
		if self.Obs.Visible():	# Statistics for display
			for agent in self.Pop:
				agent.update(infancy=self.Obs.hot_phase())	# update location for display
				# self.Obs.Positions[agent.ID] = agent.location	# Observer stores agent location 
			# ------ Observer stores social links
			self.Obs.Alliances = [(agent.ID, [T.ID for T in agent.social_signature()]) for agent in self.Pop]
			self.Obs.record(self.positions(), Window='Field')
			# self.Obs.curve('SignalLevel', self.SignalAvg())
			if self.Param('AvgFriendDistance'):	self.Obs.curve('FriendDistance', self.FriendDistance())
			Colours = ['brown', 'blue', 'red', 'green', 'white']
			for F in sorted(list(self.Features.keys())):
				self.Obs.curve(F, self.FeatureAvg(F), Color=self.Features[F][0], 
						Legend='Avg of %s' % F)

	def season_initialization(self):
		for agent in self.Pop:	agent.reinit()
	
	def interactions(self, group=None, NbInteractions=None):
		" interactions occur within a group "
		if NbInteractions is None: NbInteractions = self.Param('NbInteractions')
		if group is None: group = self.Pop
		for encounter in range(NbInteractions):
			Player, Partner = sample(group, 2)
			Player.Interact(Partner)
	
	def learning(self):
		" called at each 'run', several times per year "
		Learners = sample(self.Pop, ET.chances(self.Param('LearningProbability')/100.0, len(self.Pop)))	
		# ------ some agents learn
		for agent in self.Pop:
			agent.assessment()	# storing current scores (with possible cross-benefits)
			if agent in Learners:
				agent.Learns(self.neighbours(agent), hot=self.Obs.hot_phase())
				agent.update()	# update location for display
		for agent in self.Pop:	# now cross-benefits are completed
			agent.wins(agent.Points)	# Stores points for learning
				
	def One_Run(self):
		# This procedure is repeatedly called by the simulation thread
		# ====================
		# Display
		# ====================
		self.Obs.season()	# increments year
		# ====================
		# Interactions
		# ====================
		for Run in range(self.Param('NbRunPerYear')):	
			self.season_initialization()
			
			# ------ interactions witing groups
			GroupLength = len(self.Pop) // self.NbGroup
			if self.NbGroup > 1:
				Pop = self.Pop[:] 
				shuffle(Pop)
			else:	Pop = self.Pop
			for groupID in range(self.NbGroup):	# interaction only within groups
				group = Pop[groupID * GroupLength: (groupID + 1) * GroupLength]
				self.interactions(group)

			# ------ learning
			self.learning()

		self.display()
		return True	# This value is forwarded to "ReturnFromThread"

	def __len__(self):	return len(self.Pop)
		
		
def Start(Params=None, PopClass=Social_Population, ObsClass=Social_Observer, DumpFeatures=None, Windows='FNC'):
	if Params is None:	Params = Global()
	Observer = ObsClass(Params)   # Observer contains statistics
	Observer.setOutputDir('___Results')
	Views = []
	if 'F' in Windows:	Views.append(('Field', 770, 70, 520, 370))
	if 'N' in Windows:	Views.append(('Network', 530, 200))
	# if 'T' in Windows:	Views.append(('Trajectories', 500, 350))
	Observer.recordInfo('DefaultViews',	Views)	# Evolife should start with that window open
	# Observer.record((100, 100, 0, 0), Window='Field')	# to resize the field
	Pop = PopClass(Params, Params['NbAgents'], Observer)   # population of agents
	if DumpFeatures is None:	DumpFeatures = list(Pop.Features.keys()) + ['DistanceToBestFriend']
	Observer.recordInfo('DumpFeatures', DumpFeatures)
	BatchMode = Params['BatchMode']
	
	if BatchMode:
		##########	##########
		# Batch mode
		####################
		import Evolife.QtGraphics.Evolife_Batch  as EB
		# # # # for Step in range(Gbl['TimeLimit']):
			# # # # #print '.',
			# # # # Pop.One_Run()
			# # # # if os.path.exists('stop'):	break
		EB.Start(Pop.One_Run, Observer)
	else:
		####################
		# Interactive mode
		####################
		import Evolife.QtGraphics.Evolife_Window as EW
		" launching window "
		try:
			EW.Start(Pop.One_Run, Observer, Capabilities=Windows+'P', Options={'Background':'lightblue'})
		except Exception as Msg:
			from sys import excepthook, exc_info
			excepthook(exc_info()[0],exc_info()[1],exc_info()[2])
			input('[Entree]')
		
	Params.Dump_(Pop.Dump, Observer.get_info('ResultFile'), Observer.get_info('DumpFeatures'), 
					Observer.get_info('ExperienceID'), Verbose = not BatchMode)
	if not BatchMode:	print("Bye.......")
	# sleep(2.1)	
	return
	


if __name__ == "__main__":
	Gbl = Global()
	if Gbl['RandomSeed'] > 0:	random.seed(Gbl['RandomSeed'])
	Start(Gbl)



__author__ = 'Dessalles'
