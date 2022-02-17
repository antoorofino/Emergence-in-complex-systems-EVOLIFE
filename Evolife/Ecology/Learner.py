#!/usr/bin/env python3
##############################################################################
# EVOLIFE  http://evolife.telecom-paris.fr             Jean-Louis Dessalles  #
# Telecom Paris  2021                                      www.dessalles.fr  #
# -------------------------------------------------------------------------- #
# License:  Creative Commons BY-NC-SA                                        #
##############################################################################


##############################################################################
#  Learner                                                                   #
##############################################################################

""" EVOLIFE: Module Learner:
		Simple trial-and-error learning mechanism """

if __name__ == '__main__':  # for tests
	import sys
	sys.path.append('../..')
	# from Evolife.Scenarii.MyScenario import InstantiateScenario
	# InstantiateScenario('SexRatio')


from random import random, randint
from Evolife.Tools.Tools import boost, LimitedMemory, error


# Global elements
class Global:
	def __init__(self):
		# General functions
		# Closer pushes x towards Target
		self.Closer = lambda x, Target, Attractiveness: ((100.0 - Attractiveness) * x + Attractiveness * Target) / 100
		# Perturbate is a mutation function
		self.Perturbate = lambda x, Amplitude: x + (2 * random() - 1) * Amplitude
		# Limitate keeps x within limits
		self.Limitate = lambda x, Min, Max: min(max(x,Min), Max)
		# Decrease is a linear decreasing function between 100 and MinY
		self.Decrease = lambda x, MaxX, MinY: max(MinY, (100 - x * ((100.0 - MinY)/ MaxX)))


Gbl = Global()

class LimitedMemory_(LimitedMemory):
	def __str__(self):
		if self.past:	features = list(self.past[0][0].keys())
		Res = ''
		for b in self.past:
			Res += ','.join([f"{f[0]}:{b[0][f]:0.1f}" for f in features if f == 'Signal'])
			Res += f": {b[1]:0.1f} -- "
		return Res

class Learner:
	"	defines learning capabilities "
	def __init__(self, Features, MemorySpan=5, AgeMax=100, Infancy=0, Imitation=0, Speed=3, 
			JumpProbability=0, Conservatism=0, LearningSimilarity=10, toric=False, Start=-1):	
		self.Features = Features	# Dictionary or list of features that will be learned
		self.MemorySpan = MemorySpan
		self.Scores = LimitedMemory_(self.MemorySpan)  # memory of past benefits
		self.AgeMax = AgeMax
		self.Performance = []	# stores current performances
		self.Infancy = Infancy	# percentage of lifetime when the learner is considered a child
		self.Imitation = Imitation	# forced similarity wiht neighbouring values when learning continuous function
		self.Speed = Speed	# learning speed
		self.JumpProbability = JumpProbability
		self.Conservatism = Conservatism
		self.LearningSimilarity = LearningSimilarity
		self.Toric = toric
		self.Start = Start
		self.Reset(Newborn=False)	# individuals are created at various ages
		
	def Reset(self, Newborn=True):
		self.Age = 0 if Newborn else randint(0, self.AgeMax)	# age is random at initialization
		Features = dict()	# so that self.Features may be created as a list
		for F in self.Features:
			if self.Start == -1 or Newborn:	Features[F] = randint(0,100) 
			else: Features[F] = 100 * self.Start
		self.Features = Features
		self.Scores.reset()

	def adult(self):	return self.Age > self.AgeMax * self.Infancy / 100.0

	def feature(self, F, Value=None):
		if F is None:	F = list(self.Features.keys())[0]	
		if Value is not None:	self.Features[F] = Value
		return self.Features[F]

	def Limitate(self, x, Min, Max):
		if self.Toric: return (x % Max)
		else:	return Gbl.Limitate(x, Min, Max)
	
	
	def imitate(self, models, Feature):
		" the individual moves its own feature closer to its models' features "
		if models:
			TrueModels = [m for m in models if m.adult()]
			if TrueModels:
				ModelValues = list(map(lambda x: x.feature(Feature), TrueModels))
				Avg = float(sum(ModelValues)) / len(ModelValues)
				return Gbl.Closer(self.feature(Feature), Avg, self.Imitation)
		return self.feature(Feature)

		
	def bestRecord(self, second=False):
		" retrieve the best (or the second best) solution so far "
		if len(self.Scores) == 0:	Best = None
		elif len(self.Scores) == 1:	Best = self.Scores.last()
		else:
			# ------ retrieve the best solution so far
			past = self.Scores.retrieve()
			Best = max(past, key = lambda x: x[1])
			if second:	
				# ------ retrieve the SECOND best solution so far
				past = past[:]
				past.remove(Best)
				Best = max(past, key = lambda x: x[1])
		return Best
		
	def bestFeatureRecord(self, Feature):
		" alternative to bestRecord that aggregates similar feature values "
		if len(self.Scores) == 0:	return None
		Best = dict() 
		for i, (B1, Perf1) in enumerate(self.Scores.retrieve()):
			for j, (B2, Perf2) in enumerate(self.Scores.retrieve()):
				# if j >= i:	break	# symmetry
				dist= abs(B1[Feature] - B2[Feature]) / (0.001 +self.LearningSimilarity)
				# ------ updating Perf1 through weighted sum depending on distance
				Perf1 = (Perf1 + Perf2 / (1 + dist)) * (1 + dist)/(2 + dist)
			Best[B1[Feature]] = Perf1
		return max(Best, key=Best.get)	# return key with max value

	def avgRecord(self):
		if len(self.Scores) > 0:
			return sum([p[1] for p in self.Scores.retrieve()]) / len(self.Scores)
		else:	return 0
		
	def loser(self):
		" a looser has full experience and bad results "
		return self.Scores.complete() and self.bestRecord()[1] <= 0
		
	def explore(self, Feature, Speed, Bottom=0, Top=100):
		"   the individual changes its feature to try to get more points "
		# try:	Best = self.bestRecord(second=False)[0][Feature]
		try:	Best = self.bestFeatureRecord(Feature)
		except (TypeError, IndexError):	Best = self.Features[Feature]
		Target = self.Limitate(Gbl.Perturbate(Best, Speed), Bottom, Top)
		return round(Gbl.Closer(Target, self.feature(Feature), self.Conservatism), 2)	# Target closer to old value if conservative
		

	def Learns(self, neighbours=None, Speed=None, hot=False, BottomValue=0, TopValue=100):
		""" Learns by randomly changing current value.
			Starting point depends on previous success and on neighbours.
			If 'hot' is true, perturbation is larger for children 
		"""
		if self.Age > self.AgeMax:	self.Reset(Newborn=True)
		self.Age += 1
		# Averaging performances obtained for current feature values
		Performance = 0
		if len(self.Performance): Performance = float(sum(self.Performance)) / len(self.Performance)
		self.Performance = []	# resetting performance
		self.Scores.push((self.Features.copy(), Performance))	# storing current performance
		if self.Age == 1:	return False	# Newborn, no learning

		# (1) imitation
		FeatureNames = list(self.Features.keys()) # safer to put 'list'
		# get features closer to neighbours' values
		if self.Imitation:
			for F in FeatureNames:	self.feature(F, self.imitate(neighbours, F))

		# (2) exploration
		if Speed is None:	Speed = self.Speed
		if hot and not self.adult():	# still a kid
			LearningSpeed = Gbl.Decrease(self.Age, self.Infancy, Speed)
		else:	LearningSpeed = Speed
		if randint(0,100) < self.JumpProbability:	LearningSpeed = TopValue	# max exploration from time to time
		# compromise between current value and a perturbation of past best value
		for F in FeatureNames:
			# Pr = (F == 'Signal' and self.feature(F) == 0)	################################
			self.feature(F, self.explore(F, LearningSpeed, Bottom=BottomValue, Top=TopValue))
			# if Pr:	#################################
				# print(self.outrages, self.Scores, '\t//\t', self.feature(F))
				# print(self.bestFeatureRecord('Signal'))
		return True

	def wins(self, Points):
		"   stores a benefit	"
		self.Performance.append(Points)
	
	def __str__(self):	return str(self.Features)



			
###############################
# Local Test                  #
###############################

if __name__ == "__main__":
	print(__doc__)
	print(Learner.__doc__ + '\n\n')
	John_Doe = Learner({'F':0})
	print("John_Doe:\n")
	print(John_Doe)
	raw_input('[Return]')


__author__ = 'Dessalles'
