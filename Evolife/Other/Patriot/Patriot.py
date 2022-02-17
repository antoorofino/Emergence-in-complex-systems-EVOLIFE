#!/usr/bin/env python3
#!/usr/bin/env python3
##############################################################################
# EVOLIFE  http://evolife.telecom-paris.fr             Jean-Louis Dessalles  #
# Telecom Paris  2021                                      www.dessalles.fr  #
# -------------------------------------------------------------------------- #
# License:  Creative Commons BY-NC-SA                                        #
##############################################################################


""" Study of the emergence of uniform exagerated signals in the presence of gossip
"""

import sys
import random
sys.path.append('../../..')

import Evolife.Tools.Tools as ET
import Evolife.Ecology.Alliances as EA
import Evolife.Other.SocialNetwork.SocialSimulation as SSim

Gbl = None	# will hold global parameters

class Observer(SSim.Social_Observer):
	def __init__(self, Parameters=None):
		super().__init__(Parameters)
		L = '<br><u>Field</u>:<br>'
		L += 'Individuals are displayed by the signal they emit as a function of their quality.<br>'
		L += 'White dots are juveniles. The green curve represents the cost coefficient.<br>'
		L += '<br><u>Trajectories</u>:<br>'
		L += "x-axis: signal -- y-axis: number of outrages directed at the individual<br>"
		self.recordInfo('WindowLegends', L)
		self.recordInfo('Background', '#BBBBFF')

	def Field_grid(self):
		" initial draw: Maximal cost line "
		# G = [(0, 0, 'blue', 1, 100, 100, 'blue', 1), (100, 100, 1, 0)]
		G = [(100, 100, 1, 0)]
		Dots = [(x, 100 * Gbl['SignallingCost'] * ET.decrease(x, 100, Gbl['CostDecrease']),
				'green', 1) for x in range(Gbl['BottomCompetence'], 100) ]
		# drawing segments
		G += [x+y for (x,y) in zip(Dots[:-1], Dots[1:])]
		# drawing signal levels
		SLN = Gbl['SignalLevels']
		if SLN > 0:
			# for sl in range(1, SLN):
				# G += [(0, sl*100/SLN, 'blue', 1, 100, sl*100/SLN, 'blue', 1)]
			for sl in Gbl['Levels']:	G += [(0, sl, 'blue', 1, 100, sl, 'blue', 1)]
		return G
		
	
class Individual(SSim.Social_Individual):
	"   class Individual: defines what an individual consists of "

	def __init__(self, IdNb, maxQuality=100, features={}, parameters=None):
		self.BestSignal = 0	# best signal value in memory
		# self.GossipOpportunities = 0       # players' opportunities to gossip others may be capped
		# ------ individuals that might be admired:
		self.reputable = EA.Friend(Gbl['MaxFriends']) 
		# ------ individuals that might be despised:
		self.disreputable = EA.Friend(Gbl['MaxFriends']) 
		# ------ Social_Individual includes storage of friends:
		SSim.Social_Individual.__init__(self, IdNb, features=features, 
				maxQuality=maxQuality, parameters=Gbl, SocialSymmetry=True)	# calls Reset()
		# ------ recalibrate quality
		BQ = Gbl['BottomCompetence']
		Q = (100 * IdNb) // maxQuality
		self.Quality = (100 - BQ) * Q // 100 + BQ
		self.outrages = 0	# counts outrages directed toward self (for display)
		
	def Reset(self, Newborn=True):		
		" called by Learner when born again "
		SSim.Social_Individual.Reset(self, Newborn=Newborn)
		self.reinit()
		self.update()

	def reinit(self):	
		" called at the beginning of each year "
		if Gbl['EraseNetwork']:	
			self.forgetAll()
			self.reputable.detach()
			self.disreputable.detach()
		self.Points = 0
		self.signal = None
		# ------ Non-linearity on policing probability to avoid parasitic policing
		self.PolicingProbability = (self.feature('PolicingProbability') / 100.0) ** 4
		self.outrages = 0	# counts outrages directed toward self (for display)

	def Colour(self):
		return max(22, 27 - int(self.PolicingProbability * 5.0))

	def update(self, infancy=True):
		Colour = self.Colour()
		if infancy and not self.adult():	Colour = 'white'	# children are white
		self.BestSignal = self.bestFeatureRecord('Signal')
		if self.BestSignal is None:	self.BestSignal = 0
		self.location = (self.Quality, self.Signal(SignalValue=self.BestSignal), Colour, -1)	# -1 == negative size --> relative size instead of pixel
		# self.location = (self.Quality, self.Signal(), Colour, -1)	# -1 == negative size --> relative size instead of pixel

	def Signal(self, SignalValue=None):
		" returns the actual quality of an individual or its displayed version "
	
		def quantization(signal):
			" returns a quantized value of signal "
			for level in Gbl['Levels'][::-1]:
				if signal >= level:	return level
			return signal if signal < 0 else 0			# signal may be negative in certain implementations
	
		if SignalValue is not None:
			return quantization(SignalValue)
		if self.signal is None:		# computing signal only once 
			# ------ actual investment in displays
			self.signal = quantization(self.feature('Signal'))
		return self.signal
		
	def SignallingCost(self):
		# ------ cost coefficient decreases with quality
		C = ET.decrease(self.Quality, 100, Gbl['CostDecrease'])
		return Gbl['SignallingCost'] * C * self.Signal()
	
	def Interact(self, Partner):	
		" triadic interactions: self and Partner talk about a third party "
		SSignal = self.Signal()
		PSignal = Partner.Signal()
		Policing = (random.random() < self.PolicingProbability)
		# Gossip = False
		Gossip = False
		if Policing:
			# ----- self talks about worse third parties to Partner
			Other = self.disreputable.best_friend()	# = worst, actually, as negative scores stored 
			if Other is not None:
				Gossip = True	# self knows that some individuals signal less
				OSignal = Other.Signal()
				if PSignal > OSignal:	# yes, that guy is despicable
					Partner.disreputable.follow(Other, -OSignal)	# storing negative score
			# ----- self talks about best third parties to Partner
			if Gossip:	# only praise others if you could find someone worse than you
				Other = self.reputable.best_friend()
				if Other is not None:
					OSignal = Other.Signal()
					if PSignal < OSignal:
						Partner.reputable.follow(Other, OSignal)
		if Gossip or (random.randint(0,100) < Gbl['Visibility']):
			# ------ Partner gets an opinion about self (checks self's signal)
			# ------ The point of gossiping is to make oneself more visible 
			# ------ when being sure that one is not worst
			# # # # # # if PSignal < SSignal:	# remember better individuals
				# # # # # # Partner.reputable.follow(self, SSignal)
			# # # # # # elif PSignal > SSignal:	# remember worse individuals
				# # # # # # Partner.disreputable.follow(self, -SSignal)
			# ------ trying to establish friendship anyway
			if Partner.F_follow(0, self, SSignal):
				# ------ self worth to be Partner's friend
				if PSignal < SSignal:
					Partner.reputable.follow(self, SSignal)
			else:
				# ------ self not worth to be Partner's friend
				if PSignal > SSignal:
					Partner.disreputable.follow(self, -SSignal)
			return True
		return False
		
	def assessment(self):
		" effect of social encounters "
		self.Points -= self.SignallingCost()	# signalling cost (given a positive), paid only once
		self.Points += (Gbl['PolicingCost'] * self.feature('PolicingProbability') / 100.0)	# cost of policing
		self.Points = int(self.Points)
		# for G in self.reputable:	G.Points += Gbl['AdmirationImpact']
		# for W in self.disreputable:	
			# W.Points += Gbl['ContemptImpact']
			# W.outrages += 1
		# # # # # if len(self.disreputable):	print([(w.Signal(), w.Points) for w in self.disreputable])
		best = self.reputable.best_friend()
		worst = self.disreputable.best_friend()
		if best is not None:	best.Points += Gbl['AdmirationImpact']
		if worst is not None:	
			worst.Points += Gbl['ContemptImpact']
			worst.outrages += 1
		for F in self.friends.names():	F.Points += Gbl['FriendshipImpact']
		
	def __str__(self):
		return f"{self.ID}[{self.Signal():0.1f} {int(self.Points)}]"
		
class Population(SSim.Social_Population):
	" defines the population of agents "

	def __init__(self, parameters, NbAgents, Observer):
		" creates a population of agents "
		# ------ Learnable features
		Features = dict()
		Features['PolicingProbability'] = ('brown',)	# ability to gossip
		Features['Signal'] = ('blue',)	# propensity to signal one's quality
		# Features['Visibility'] = ('white',)	# makes signal visible
		SSim.Social_Population.__init__(self, Gbl, NbAgents, Observer, 
			IndividualClass=Individual, features=Features)

	def interactions(self, group):
		" interactions occur within a group "
		NbI = Gbl['NbInteractions']
		# super().interactions(group, NbInteractions=int(NbI * len(group) ** 2 / 2))
		for encounter in range(NbI):
			random.shuffle(group)
			for Player in group:
				for Partner in group:
					if Partner.ID != Player.ID:
						Player.Interact(Partner)
			
	def display(self):
		super().display()
		if self.Obs.Visible():	# Statistics for display
			# Worsts = []
			for A in self.Pop:
				Colour = A.Colour()
				TrPosition = (A.Signal()+10*random.random(), A.outrages, Colour, 7)
				# TrPosition = (A.Signal()+10*random.random(), 100 + A.Points, Colour, 7)
				self.Obs.record((A.ID, TrPosition), Window='Trajectories')
				# Worsts.append(A.disreputable.worst())
			# # Worsts = set(Worsts)
			# # for A in Worsts:	print(A, end=' ', flush=True)
			# # print()
			# # print()
				
	def Dump(self, Slot):
		""" Saving investment in signalling for each adult agent
			and then distance to best friend for each adult agent having a best friend
		"""
		if Slot == 'DistanceToBestFriend':
			D = [(agent.Quality, "%d" % abs(agent.best_friend().Quality - agent.Quality)) for agent in self.Pop if agent.adult() and agent.best_friend() is not None]
			D += [(agent.Quality, " ") for agent in self.Pop if agent.best_friend() == None or not agent.adult()]
		else:
			D = [(agent.Quality, "%2.03f" % agent.feature(Slot)) for agent in self.Pop]
		return [Slot] + [d[1] for d in sorted(D, key=lambda x: x[0])]
		
def Start(Params=None):
	global Gbl
	if Params is not None: 	Gbl = Params
	


if __name__ == "__main__":
	Gbl = SSim.Global('___Patriot.evo')
	B = Gbl['LevelBase']	# not evenly spaced levels if B is nonzero
	if B > 0:	
		Gbl['Levels'] = [B**level * 90/B**Gbl['SignalLevels'] 
				for level in range(1, Gbl['SignalLevels']+1)]
	elif B < 0:
		Gbl['Levels'] = sorted([90 - abs(B)**level * 90/B**Gbl['SignalLevels'] 
				for level in range(1, Gbl['SignalLevels']+1)])
	else:	Gbl['Levels'] = [level * 90/Gbl['SignalLevels'] 
				for level in range(1, Gbl['SignalLevels']+1)]
	if Gbl['BatchMode'] == 0:	
		print(__doc__)
		print('Levels:', list(map(int, Gbl['Levels'])))
	Start()
	SSim.Start(Params=Gbl, PopClass=Population, ObsClass=Observer, Windows='FCT')


__author__ = 'Dessalles'
