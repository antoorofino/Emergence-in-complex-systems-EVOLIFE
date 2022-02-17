#!/usr/bin/env python3
##############################################################################
# EVOLIFE  http://evolife.telecom-paris.fr             Jean-Louis Dessalles  #
# Telecom Paris  2021                                      www.dessalles.fr  #
# -------------------------------------------------------------------------- #
# License:  Creative Commons BY-NC-SA                                        #
##############################################################################
##############################################################################
"""  physical display (Screen and monitors)                                """
##############################################################################

try:	from PyQt5 import QtWidgets
except ImportError:				# compatibility with PyQt4
		from PyQt4 import QtGui as QtWidgets

class Screen_:
	" Stores characteristics of physical display "
	
	def __init__(self, MainApp):
		self.width = 1920	# will be changed
		self.height = 1080	# will be changed
		self.ratio = 1		# comparison with default screen
		screen_rect = MainApp.desktop().screenGeometry()
		self.ratio = screen_rect.width() / self.width
		self.width, self.height = screen_rect.width(), screen_rect.height()
		self.displays = []
		for Disp in range(0,8):
			D = QtWidgets.QDesktopWidget().screenGeometry(Disp)
			if D:	self.displays.append(D)
			else:	break
		self.currentScreen = 0
		# print(self.displays)
		
	def resize(self, *Coord):
		return list(map(lambda x: int(x * self.ratio), Coord))
		
	def locate(self, *Coord):
		" applies display ratio for high definition screen and optional screen change "
		return self.changeScreen(list(self.resize(*Coord)))
	
	def switchScreen(self):
		self.currentScreen = len(self.displays) - self.currentScreen - 1
	
	def changeScreen(self, Coord):
		# print('Change coordinates:', Coord, end=' ')
		Coord = [Coord[0] + self.displays[self.currentScreen].left(), 
				 Coord[1] + self.displays[self.currentScreen].top()] \
				 + Coord[2:]
		# print('to ', Coord)
		return Coord
		
__author__ = 'Dessalles'
