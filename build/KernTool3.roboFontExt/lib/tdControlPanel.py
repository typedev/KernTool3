# -*- coding: utf-8 -*-


import sys
from vanilla import *
from mojo.UI import *
from fontParts.world import CurrentFont, RGlyph
from defconAppKit.windows.baseWindow import BaseWindowController
# from mojo.canvas import Canvas
from mojo.drawingTools import *
from AppKit import *

import importlib
from mojo.canvas import *

import tdCanvasKeysDecoder
importlib.reload(tdCanvasKeysDecoder)
from tdCanvasKeysDecoder import *

from tdCanvasKeysDecoder import decodeCanvasKeys
from mojo.drawingTools import *
from fontParts.world import CurrentFont
# from vanilla.nsSubclasses import getNSSubclass
from defconAppKit.windows import *

import tdKernToolEssentials
importlib.reload(tdKernToolEssentials)
from tdKernToolEssentials import *

'''
title
hotkey
selected
callback

'''
latletters = 'abcdefghijklmnopqrstuvwxyz[ ]:'

LEVEL_FULL = chr(int('2981', 16)) #2589  25A0 25C9
LEVEL_EMPTY = chr(int('26AC', 16)) # 2591  25A1 25CB


class TDControlPanel(VanillaBaseObject):
	nsViewClass = NSView

	def __init__ (self, posSize, parentWindow, selectionCallback=None, keyPressedCallback=None, active = True):
		xw, yw, tx, ty = posSize
		self.Xpos = xw
		self._viewArray = []
		self.parentWindow = parentWindow
		self._letterStep = 7
		self._letterStepLine = 15
		self._viewFontName = '.SFCompactText-Regular'#'.SFCompactText-Regular' #'.AppleSDGothicNeoI-Regular' #'Menlo'
		self._viewFontNameDMselected = '.SFCompactText-Semibold'
		self._viewFontNameSymbols = '.SFCompactText-Regular'#'AppleSymbols'#'.SFCompactText-Regular' #'.LucidaGrandeUI' #'.Keyboard'
		self._viewFontSize = 12
		self._scaleUI = 1
		self.darkmode = KERNTOOL_UI_DARKMODE
		self.darkmodeWarm = KERNTOOL_UI_DARKMODE_WARMBACKGROUND
		self.maxX = 0

		self.color_TXT = COLOR_BLACK
		self.color_SEPARATOR = COLOR_GREY_30
		if self.darkmode:
			self.color_TXT = (COLOR_GREY_20)
			self.color_SEPARATOR = COLOR_GREY_50

		self._clicked = False
		self._mouseOn = False
		self._active = active

		self._selectionCallback = selectionCallback
		self._keyPressedCallback = keyPressedCallback
		# self._mouseMovedCallback = mouseMovedCallback
		self._setupView(self.nsViewClass, (xw, yw, tx, ty))  # (0, 0, -0, 106)
		self.controlCanvas = Canvas((0, 0, -0, -0),
		                            delegate = self,  # canvasSize = (100, 101),
		                            hasHorizontalScroller = False,
		                            hasVerticalScroller = False,
		                            autohidesScrollers = True,
		                            # backgroundColor = NSColor.whiteColor(),
		                            # acceptsMouseMoved = True
		                            )
		# self.parentWindow.acceptsMouseMoved()
		# self.mouseMoved = self.controlCanvas.getNSView().acceptsMouseMoved()
		self.controlCanvas.scrollView.getNSScrollView().setBorderType_(NSNoBorder)
		self.controlCanvas.update()

	def addControlItem (self, title=None, hotkey=None,
	                    command=None, callback=None,
	                    visible=True, callbackValue=None):
		uuidControl = getUniqName()
		self._viewArray.append({'type': 'button',
		                        'title': title,
		                        'uuidControl': uuidControl,
		                        'hotkey': hotkey,
		                        'command': command,
		                        'callback': callback,
		                        'selected': False,
		                        'clicked': False,
		                        'visible': visible,
		                        'callbackValue': callbackValue,
		                        'color': self.color_TXT,
		                        'enable': True,
		                        'x0': 0,
		                        'x1': 0})
		self.controlCanvas.update()
		return uuidControl

	def addMenuSeparator (self, type = 'default'):
		uuidControl = getUniqName()
		if type == 'default':
			title = chr(int('2502', 16))
		elif type == 'bullet':
			title = chr(int('2219',16))
		elif type == 'colon':
			title = chr(int('003A',16))
		else:
			title = type
		self._viewArray.append({'type': 'button',
		                        'title': title,
		                        'uuidControl': uuidControl,
		                        'hotkey': None,
		                        'command': None,
		                        'callback': None,
		                        'selected': False,
		                        'clicked': False,
		                        'visible': True,
		                        'callbackValue': None,
		                        'color': self.color_SEPARATOR,
		                        'enable': True,
		                        'x0': 0,
		                        'x1': 0})
		self.controlCanvas.update()
		return uuidControl

	def _levelControlCallback (self, info):
		parentUUID, uuidlevel, callbackExternal, callbackvalue = info
		for idx, item in enumerate(self._viewArray):
			if item['type'] == 'level':
				if item['parentUUID'] == parentUUID:
					# print item['callbackValue'], callbackvalue
					if item['callbackValue'] <= callbackvalue:
						item['title'] = LEVEL_FULL
					# print 'full', item['title']
					else:
						item['title'] = LEVEL_EMPTY
					# print 'empty',item['title']
		if callbackExternal and item['enable']:
			callbackExternal(callbackvalue)
		# break
		self.controlCanvas.update()

	def addLevelControlItem (self, title, hotkey_down=None, hotkey_up=None,
	                         command_down=None, command_up=None,
	                         callback=None, min_level=0, max_level=100, step_level=10, value=50,
	                         visible=True):
		title += ':'

		self._viewArray.append({'type': 'button',
		                        'title': title,
		                        'uuidControl': getUniqName(),
		                        'hotkey': None,
		                        'command': None,
		                        'callback': None, #callback,
		                        'selected': False,
		                        'clicked': False,
		                        'visible': visible,
		                        'callbackValue': None,
		                        'color': self.color_TXT,
		                        'enable': True,
		                        'x0': 0,
		                        'x1': 0})
		# d1 = (max_level - min_level) / step_level

		uuidControl = getUniqName()
		for i in range(min_level, max_level, step_level):
			if i < value:
				titleLevel = LEVEL_FULL
			else:
				titleLevel = LEVEL_EMPTY
			self._viewArray.append({'type': 'level',
			                        'title': titleLevel,
			                        'hotkey': None,
			                        'command': None,
			                        'callback': self._levelControlCallback,
			                        'callbackExternal': callback,
			                        'selected': False,
			                        'clicked': False,
			                        'visible': visible,
			                        'callbackValue': i,
			                        'color': self.color_TXT,
			                        'parentUUID': uuidControl,
			                        'uuidControl': getUniqName(),
			                        'enable': True,
			                        'x0': 0,
			                        'x1': 0})
		# self._viewArray.append({'type': 'button',
		#                         'title': ' ',
		#                         'uuidControl': getUniqName(),
		#                         'hotkey': None,
		#                         'command': None,
		#                         'callback': None,
		#                         'selected': False,
		#                         'clicked': False,
		#                         'visible': visible,
		#                         'callbackValue': None,
		#                         'color': self.color_TXT,
		#                         'x0': 0,
		#                         'x1': 0})
		self.controlCanvas.update()
		return uuidControl

	def addSwitchControlItem(self, title=None, hotkey_down=None, hotkey_up=None,
	                         command_down=None, command_up=None,
	                         callback=None,
	                         switchers = None, # list of switchers ('switch 0','switch 0',...)
	                         visible=True):
		t =''
		if title:
			t = title
		self._viewArray.append({'type': 'button',
		                        'title': t,
		                        'uuidControl': getUniqName(),
		                        'hotkey': None,
		                        'command': None,
		                        'callback': None,
		                        'selected': False,
		                        'clicked': False,
		                        'visible': visible,
		                        'callbackValue': None,
		                        'color': self.color_TXT,
		                        'enable': True,
		                        'x0': 0,
		                        'x1': 0})
		uuidControl = getUniqName()
		if title:
			self._viewArray.append({'type': 'button',
			                        'title': ':',
			                        'uuidControl': uuidControl,
			                        'hotkey': None,
			                        'command': None,
			                        'callback': None,
			                        'selected': False,
			                        'clicked': False,
			                        'visible': True,
			                        'callbackValue': None,
			                        'color': self.color_SEPARATOR,
			                        'enable': True,
			                        'x0': 0,
			                        'x1': 0})

		for idx, switcher in enumerate(switchers):
			tswitch, value = switcher
			self._viewArray.append({'type': 'level',
			                        'title': tswitch,
			                        'hotkey': None,
			                        'command': None,
			                        'callback': self._switchControlCallback,
			                        'callbackExternal': callback,
			                        'selected': False,
			                        'clicked': False,
			                        'visible': visible,
			                        'callbackValue': value,
			                        'color': self.color_TXT,
			                        'parentUUID': uuidControl,
			                        'uuidControl': getUniqName(),
			                        'enable': True,
			                        'x0': 0,
			                        'x1': 0})
			if idx != len(switchers)-1:
				self._viewArray.append({'type': 'button',
				                        'title': ':',
				                        'uuidControl': uuidControl,
				                        'hotkey': None,
				                        'command': None,
				                        'callback': None,
				                        'selected': False,
				                        'clicked': False,
				                        'visible': True,
				                        'callbackValue': None,
				                        'color': self.color_SEPARATOR,
				                        'enable': True,
				                        'x0': 0,
				                        'x1': 0})


		self.controlCanvas.update()
		return uuidControl

	def _switchControlCallback(self, info):
		parentUUID, uuidlevel, callbackExternal, callbackvalue = info
		# print (info)
		for idx, item in enumerate(self._viewArray):
			if item['type'] == 'level':
				if item['parentUUID'] == parentUUID and item['uuidControl'] == uuidlevel:
					# print item['callbackValue'], callbackvalue
					item['selected'] = True
				elif item['parentUUID'] == parentUUID and item['uuidControl'] != uuidlevel:
					item['selected'] = False
		if callbackExternal and item['enable']:
			callbackExternal(callbackvalue)
		# break
		self.controlCanvas.update()

	def setSwitchItem(self, uuidControl, switch = None):
		for idx, item in enumerate(self._viewArray):
			if item['type'] == 'level':
				if item['parentUUID'] == uuidControl and item['title'] == switch:
					# print item['callbackValue'], callbackvalue
					item['selected'] = True
				elif item['parentUUID'] == uuidControl and item['title'] != switch:
					item['selected'] = False
		self.controlCanvas.update()


	def addLabelItem (self, title=None, value='',
	                  visible=True, separator = ':'):
		title += separator
		self._viewArray.append({'type': 'button',
		                        'title': title,
		                        'uuidControl': getUniqName(),
		                        'hotkey': None,
		                        'command': None,
		                        'callback': None,
		                        'selected': False,
		                        'clicked': False,
		                        'visible': visible,
		                        'color': self.color_TXT,
		                        # 'callbackValue': callbackValue,
		                        'enable': True,
		                        'x0': 0,
		                        'x1': 0})
		uuidControl = getUniqName()
		self._viewArray.append({'type': 'label',
		                        'title': str(value),
		                        'hotkey': None,
		                        'command': None,
		                        'callback': None,
		                        'selected': False,
		                        'clicked': False,
		                        'visible': visible,
		                        'parentUUID': uuidControl,
		                        'color': self.color_TXT,
		                        # 'callbackValue': callbackValue,
		                        'enable': True,
		                        'x0': 0,
		                        'x1': 0})
		# self._viewArray.append({'type': 'button',
		#                         'title': ' ',
		#                         'uuidControl': getUniqName(),
		#                         'hotkey': None,
		#                         'command': None,
		#                         'callback': None,
		#                         'selected': False,
		#                         'clicked': False,
		#                         'visible': visible,
		#                         'callbackValue': None,
		#                         'color': self.color_TXT,
		#                         'x0': 0,
		#                         'x1': 0})
		self.controlCanvas.update()
		return uuidControl

	def setLabelValue (self, uuidLabel, value, color = None):
		colorlbl = COLOR_BLACK

		if self.darkmode:
			colorlbl = self.color_TXT
		if color:
			colorlbl = color

		for idx, item in enumerate(self._viewArray):
			if item['type'] == 'label':
				if item['parentUUID'] == uuidLabel:
					item['title'] = str(value)
					item['color'] = colorlbl
				# break
		self.controlCanvas.update()

	def selectControlItem (self, uuidControl):
		for idx, item in enumerate(self._viewArray):
			if item['uuidControl'] == uuidControl:
				item['selected'] = True
			# self._viewArray[idx]['selected'] = True
		self.controlCanvas.update()

	def deselectControlItem (self, uuidControl):
		for idx, item in enumerate(self._viewArray):
			if item['uuidControl'] == uuidControl:
				item['selected'] = False
			# self._viewArray[idx]['selected'] = False
		self.controlCanvas.update()

	def setStateItem (self, uuidControl, state=False):
		if state:
			self.selectControlItem(uuidControl)
		else:
			self.deselectControlItem(uuidControl)

	def enableControlItem(self, uuidControl, state=True):
		for idx, item in enumerate(self._viewArray):
			if item['uuidControl'] == uuidControl or ('parentUUID' in item and item['parentUUID'] == uuidControl):
				item['enable'] = state
		self.controlCanvas.update()


	def keyDown (self, event):
		keypress = decodeCanvasKeys(event.keyCode(), event.modifierFlags())
		commands = translateKeyCodesToKernToolCommands(keypress)
		# print commands
		for item in self._viewArray:
			if item['command'] == commands['command']:
				if item['callbackValue'] and item['enable']:
					# print item['callbackValue']
					item['callback'](item['callbackValue'])
				else:
					item['callback']()
				break
	#
	# def mouseMoved (self, event):
	# 	print (event)
	#
	# 	if self._mouseMovedCallback:
	# 		self._mouseMovedCallback(event)

	def mouseEntered(self , event):
		self._mouseOn = True
		self.controlCanvas.update()

	def mouseExited(self, event):
		self._mouseOn = False
		self.controlCanvas.update()



	def mouseDown (self, event):
		# print event
		X_window_pos = event.locationInWindow().x
		# print('xW', X_window_pos)
		X_local_pos = self.controlCanvas.scrollView.getNSScrollView().documentVisibleRect().origin.x
		# print('xL', X_local_pos)
		x = X_window_pos + X_local_pos - self._letterStep - self.Xpos
		# print ('x',x)
		# print ('XposW',self.Xpos)
		for idx, item in enumerate(self._viewArray):
			x0 = item['x0'] * self._scaleUI - 5
			x1 = (item['x1'] - 5) * self._scaleUI
			if x0 < x and x < x1:
				if item['callback'] and item['enable']:
					self.controlCanvas.update()

					if item['type'] == 'button':
						if item['callbackValue']:
							item['clicked'] = True
							# self.controlCanvas.update()
							item['callback'](item['callbackValue'])
							# item['clicked'] = False
							self.controlCanvas.update()

						else:
							# item['clicked'] = True
							# self.controlCanvas.update()
							item['callback']()
							# item['clicked'] = False
							# self.controlCanvas.update()

					elif item['type'] == 'level':
						item['callback'](
								(item['parentUUID'], item['uuidControl'], item['callbackExternal'], item['callbackValue']))

					break

		self.controlCanvas.update()

	def mouseUp(self, event):
		for item in self._viewArray:
			item['clicked'] = False
			self.controlCanvas.update()
	#
	# def keyUp(self, event):
	# 	for item in self._viewArray:
	# 		item['clicked'] = False
	# 	self.controlCanvas.update()

	def recalculateFrame (self, canvaswidth=None):
		scalefactor = self._scaleUI
		if canvaswidth:
			visibleWidth = canvaswidth
		else:
			visibleWidth = self.controlCanvas.scrollView.getNSScrollView().documentVisibleRect().size.width
		self.visibleWidth = visibleWidth
		visibleHeight = self.controlCanvas.scrollView.getNSScrollView().documentVisibleRect().size.height

		self.controlCanvas._view.setFrame_(NSMakeRect(0, 0, visibleWidth + 20, visibleHeight))
		self.maxX = visibleWidth -20

	def draw (self):
		# self.recalculateFrame()

		visibleWidth = self.controlCanvas.scrollView.getNSScrollView().documentVisibleRect().size.width
		visibleHeight = self.controlCanvas.scrollView.getNSScrollView().documentVisibleRect().size.height
		if visibleWidth < self.maxX:
			y = 4
			self._scaleUI = 0.8
		elif visibleWidth >= self.maxX:
			y = 1.5
			self._scaleUI = 1
		self.recalculateFrame()

		def _text (textToDraw, x, y):
			# for letter in textToDraw:
			# 	nx, ny = textSize(letter)
			# 	text(letter, (x, y))
			# 	x += nx
			nx, ny = textSize(textToDraw)
			text(textToDraw, x,y)
			return nx+x

		stroke(0, 0, 0, 0)
		strokeWidth(0)

		color_TXT = self.color_TXT
		fillRGB((.96, .96, .96, 1))
		color_SELECT = COLOR_KERN_VALUE_POSITIVE
		color_HOTKEY = COLOR_GREY_50
		color_MOUSEON = (0,0,.7,1)#(.3,.3,.7,1)
		# if self._mouseOn and self._active:
		# 	fillRGB((1, 1, 1, 1))
		# self.darkmode = True
		if self.darkmode:
			fillRGB((0.20,.20,.20,1))
			color_TXT = COLOR_GREY_50
			color_HOTKEY = COLOR_GREY_50
			color_SELECT = (1,.6,.2,1)
			color_MOUSEON = (1,1,1,1)


		rect(0,0,visibleWidth,visibleHeight)
		scale(self._scaleUI)
		x = 10
		for idx, item in enumerate(self._viewArray):
			if item['visible']:

				# if item['selected'] and self.darkmode:
				# 	font(self._viewFontName, fontSize = self._viewFontSize) #DMselected
				# else:
				font(self._viewFontName, fontSize = self._viewFontSize)
				item['x0'] = x - 5
				fillRGB(color_TXT)
				if item['color']:
					fillRGB(item['color'])


				if item['callback'] and self._mouseOn and self._active:
					fillRGB(color_MOUSEON)
				if item['selected']:
					fillRGB(color_SELECT)
				if item['type'] == 'level':
					font(self._viewFontNameSymbols, fontSize = self._viewFontSize)
				if item['type'] == 'level' and self._mouseOn and item['title'] == LEVEL_FULL:
					fillRGB(color_SELECT)
					# if item['callback'] and self._mouseOn:
					# 	# bold = '-Bold'
					# 	fillRGB((.1,.3,.1,1))
						# font(self._viewFontName + bold, fontSize = self._viewFontSize)
				if not item['enable']:
					fillRGB(COLOR_GREY_50)
				x = _text(item['title'], x, y)

				if item['title'] != '': x += 2

				if item['hotkey']:
					fillRGB(color_HOTKEY)
					font(self._viewFontNameSymbols, fontSize = self._viewFontSize)
					hotkey = '[%s]' % item['hotkey']
					x = _text(hotkey, x, y)
					item['x1'] = x + 5
					x += self._letterStep
				else:
					item['x1'] = x
		self.maxX = x + 10
		# self.mouseExited(None)


if __name__ == "__main__":
	class TestControlWindow(BaseWindowController):
		def __init__ (self):
			self.w = Window((800, 200), "Test Controls", minSize = (200, 100))
			self.w.menuMain = TDControlPanel((5, 5, -5, 17),  # -160
			                                 parentWindow = self,
			                                 selectionCallback = None,
			                                 keyPressedCallback = None,
			                                 # darkmode = True
			                                 )
			self.w.menuMain.addControlItem(title = 'Menu Command 1',
			                               callbackValue = 'command 1',
			                               hotkey = 'E',
			                               callback = self.menuCallback,
			                               )
			self.w.menuMain.addControlItem(title = 'Menu Command 2',
			                               callbackValue = 'command 2',
			                               hotkey = 'D',
			                               callback = self.menuCallback,
			                               )
			# self.w.menuMain.addMenuSeparator()

			self.w.label = self.w.menuMain.addLabelItem(title = 'label title', value = 'any text')

			self.w.menuMain.addMenuSeparator()
			self.w.menuMain.addLevelControlItem(title = 'Level Control',
		                                         min_level = 0,
		                                         max_level = 10,
		                                         step_level = 1,
		                                         value = 5,
		                                         callback = self.levelCallback)
			self.w.menuMain.addMenuSeparator()

			self.switch1 = self.w.menuMain.addSwitchControlItem(title = 'Chose',
			                                                    switchers = (('10','cmd10'),
			                                                                 ('20','cmd20'),
			                                                                 ('30','cmd40')),
			                                                    callback = self.switchCallback1)
			self.w.menuMain.addMenuSeparator()

			self.w.menuMain.setSwitchItem(self.switch1, '20')

			self.w.menuMain.addSwitchControlItem( switchers = (('A','switch to A'),
			                                                   ('B','switch to B'),
			                                                   ('C','switch to C')),
			                                      callback = self.switchCallback2)
			self.w.menuMain.addMenuSeparator()


			self.w.open()




		def menuCallback(self, command):
			print (command)
			self.w.menuMain.setLabelValue(self.w.label, command)

		def levelCallback(self, value):
			print (value)

		def switchCallback1(self, value):
			print ('switch control1', value)

		def switchCallback2(self, value):
			print ('switch control2', value)



	TestControlWindow()