# -*- coding: utf-8 -*-


from vanilla import *
import importlib
from AppKit import *
from fontTools.pens.cocoaPen import CocoaPen
from mojo.canvas import Canvas
from mojo.drawingTools import *
from fontParts.world import CurrentFont
from lib.eventTools.eventManager import postEvent, publishEvent
from mojo.events import addObserver, removeObserver
from vanilla.dialogs import getFile
import codecs, sys, os
from defconAppKit.controls.glyphCollectionView import GlyphCollectionView

import tdCanvasKeysDecoder
importlib.reload(tdCanvasKeysDecoder)
from tdCanvasKeysDecoder import decodeCanvasKeys, decodeModifiers

import tdKernToolEssentials
importlib.reload(tdKernToolEssentials)
from tdKernToolEssentials import *

import tdMenuAdvanced
importlib.reload(tdMenuAdvanced)
from tdMenuAdvanced import MenuDialogWindow

import tdPairsMaker
importlib.reload(tdPairsMaker)
from tdPairsMaker import PairsBuilderDialogWindow

import tdControlPanel
importlib.reload(tdControlPanel)
from tdControlPanel import TDControlPanel

import tdGlyphparser
importlib.reload(tdGlyphparser)

import tdGroupViews
importlib.reload(tdGroupViews)
from tdGroupViews import *

import tdExceptionView
importlib.reload(tdExceptionView)
from tdExceptionView import *

# import tdLangSet
# importlib.reload(tdLangSet)
# from tdLangSet import TDLangSet

class TDKernObserver(VanillaBaseObject):
	nsViewClass = NSView

	def __init__ (self, posSize, window=None,
	              selectionCallback=None, refreshCallback=None, commandCallback=None, showSelectionBars=True):
		xw, yw, tx, ty = posSize
		self._window = window
		self._linesToDisplay = []
		self._font = None
		self.fontID = None
		self._viewArray = []
		self._hashOfPairs = {}
		self._currentLinesState = []
		self._pairsToDisplay = {}
		self._selectedBlock = 0
		self.currentPair = ()
		self.currentPairForKern = ()
		self.lastValue = 0
		self.lastMultiply = []
		self._selectedLine = 0
		self._positionYselected = 0
		self.prefix = None
		self.postfix = None
		self.leftselection = []
		self.rightselection = []
		self._lineSize = 1800  # 1800 # 1800=1000upm; 2400=2000upm
		self.Ygap = 150  # - yw*2
		self.shiftX = 200
		self.hashKernDic = None
		self.touchFlag = False
		self.useAutoKern = False
		self._scalefactorUI = .09
		self.scaleStep = 1.2
		self.lineCount = 0
		self.maxX = 0
		self.maxXX = 0
		self._lastGlyphXpos = 0
		self._hashOfSelectedBlock = []
		self._hashOfSelectedLine = []
		self._idxSelectedGlyph = 0
		self._kernValueCopy = None

		# save state for PairsBuilder
		self.PB_leftList = []
		self.PB_rightList = []
		self.PB_patternLeft = ''
		self.PB_patternRight = ''

		self.toucheMode = False
		self.valuesMode = True
		self.lightmode = False
		self.showInfo = False
		self.showKerning = True
		self.showSelectionBars = showSelectionBars

		self.highLevelLoaded = False

		self._selectionCallback = selectionCallback
		self._refreshCallback = refreshCallback
		self._commandCallback = commandCallback
		self.showselection = False

		self.observerID = getUniqName(6)

		self.macos = MACOS_VERSION

		self.darkmode = KERNTOOL_UI_DARKMODE
		self.darkmodeWarm = KERNTOOL_UI_DARKMODE_WARMBACKGROUND
		# self.langSet = TDLangSet()

		self._setupView(self.nsViewClass, (xw, yw, tx, ty))  # (0, 0, -0, 106)
		self.canvas = Canvas((0, 0, -0, -0),
		                     delegate = self,  # canvasSize = (100, 101),
		                     hasHorizontalScroller = True,
		                     hasVerticalScroller = True,
		                     autohidesScrollers = False,
		                     backgroundColor = NSColor.whiteColor(),
		                     drawsBackground = False,
		                     # acceptsMouseMoved = True
		                     )

		self.canvas.scrollView.getNSScrollView().setBorderType_(NSNoBorder)
		self.visibleWidth = 1100
		self.canvas.update()

	def setFont (self, font, hashKernDic):
		self.hashKernDic = hashKernDic
		self._font = font
		self.fontID = getFontID(self._font)
		if self._font.info.unitsPerEm < 1999:
			self._lineSize = 1800
		else:
			self._lineSize = 2400
		self.leftselection = []
		self.rightselection = []
		self.prefix = []
		self.postfix = []

	def setSize (self, size=.1):
		self._scalefactorUI = size
		self.compileLines()
		self.canvas.update()

	def setLines (self, prefix=None, left=None, right=None, postfix=None, pairsperline = None):
		self.leftselection = left
		self.rightselection = right
		self._currentLinesState = []
		idxLine = 0
		countpairs = 1
		for leftglyph in self.leftselection:
			line = []
			for rightglyph in self.rightselection:
				if prefix:
					for prefixglyph in prefix:
						if prefixglyph != '':
							line.append('%s.%s' % (prefixglyph, getUniqName()))
				line.append('%s.%s' % (leftglyph, getUniqName()))
				line.append('%s.%s' % (rightglyph, getUniqName()))
				if postfix:
					for postfixglyph in postfix:
						if postfixglyph != '':
							line.append('%s.%s' % (postfixglyph, getUniqName()))

				if pairsperline:
					if countpairs == pairsperline:
						countpairs = 1
						self._currentLinesState.append({'line': line,
						                                'basic': leftglyph,
						                                'idxLine': idxLine,
						                                'Ypos': 0})
						line = []
					else:
						countpairs += 1
			if pairsperline:
				if line:
					self._currentLinesState.append({'line': line,
					                                'basic': leftglyph,
					                                'idxLine': idxLine,
					                                'Ypos': 0})
				countpairs = 1
				idxLine += 1
			if not pairsperline:
				idxLine += 1
				# line.append('%s.%s' % (leftglyph, getUniqName()))
				self._currentLinesState.append({'line': line,
				                                'basic': leftglyph,
				                                'idxLine': idxLine,
				                                'Ypos': 0})
		self.compileLines()
		self.canvas.update()
		self.setCurrentPair(0)

	def getPairsListFromPairsBuilderDialog (self, patternLeft=None,
	                                        leftList=None,
	                                        rightList=None,
	                                        patternRight=None,
	                                        text=None, command='lines', pairsperline = None):
		if command == 'lines':
			self.PB_leftList = leftList
			self.PB_rightList = rightList
			self.PB_patternLeft = patternLeft
			self.PB_patternRight = patternRight
			self.setLines(prefix = patternLeft,
			              left = leftList,  # CurrentFont().selection,
			              right = rightList,  # CurrentFont().selection,
			              postfix = patternRight,
			              pairsperline = pairsperline)
		elif command == 'text':
			self.PB_leftList = leftList
			self.PB_rightList = rightList
			self.PB_patternLeft = patternLeft
			self.PB_patternRight = patternRight
			self.setGlyphs(notification = {'glyphsLine': text})
		elif command == 'glyphsready':
			self.PB_leftList = leftList
			self.PB_rightList = rightList
			self.PB_patternLeft = patternLeft
			self.PB_patternRight = patternRight
			self.setGlyphs(notification = {'glyphsLine': text, 'glyphsready': True})

	def setGlyphs (self, notification):
		if notification['fontID'] != self.fontID: return
		self.setFont(self._font, hashKernDic = self.hashKernDic)
		need_covertion = True
		if 'glyphsready' in notification and notification['glyphsready']:
			need_covertion = False
		if 'lines' in notification and notification['lines']:
			self.PB_leftList = notification['leftList']
			self.PB_rightList = notification['rightList']
			self.PB_patternLeft = notification['patternLeft']
			self.PB_patternRight = notification['patternRight']
			self.setLines(prefix = self.PB_patternLeft,
			              left = self.PB_leftList,  # CurrentFont().selection,
			              right = self.PB_rightList,  # CurrentFont().selection,
			              postfix = self.PB_patternRight,
			              pairsperline = notification['pairsperline'])
			return

		text = notification['glyphsLine']
		if not text: return
		self._currentLinesState = []
		lines = text.split('\\n')
		prevbasic = None
		for idxLine, line in enumerate(lines):
			tline = []
			basicglyph = None

			if need_covertion:
				for glyphName in tdGlyphparser.translateText(self._font, line):
					if glyphName and '00AD' not in glyphName:
						tline.append('%s.%s' % (glyphName, getUniqName()))
			else:
				for glyphName in line.split('/'):
					if glyphName and '00AD' not in glyphName:
						tline.append('%s.%s' % (glyphName, getUniqName()))
			if tline:
				self._currentLinesState.append({'line': tline,
				                                'basic': basicglyph,
				                                'idxLine': idxLine + 1,
				                                'Ypos': 0})
		self.compileLines()
		self.canvas.update()
		self.setCurrentPair(0)
		if 'targetpair' in notification and notification['targetpair']:
			cl , cr = notification['targetpair']
			if cl and cr:
				self.findFirstPair((cl,cr))



	def loadText (self, filepath=None):
		if filepath:
			self._currentLinesState = []

			filetxt = codecs.open(filepath[0], 'r', encoding = 'utf-8')
			for idxLine, line in enumerate(filetxt):
				line = line.rstrip()  # .split('/')'\n\r'
				if not line.startswith('#') and line != '':
					tline = []
					for glyphName in tdGlyphparser.translateText(self._font, line):
						if '00AD' not in glyphName:
							tline.append('%s.%s' % (glyphName, getUniqName()))
					if tline:
						self._currentLinesState.append({'line': tline,
						                                'basic': None,
						                                'idxLine': idxLine + 1,
						                                'Ypos': 0
						                                })
			filetxt.close()
			self.compileLines()
			self.canvas.update()
			self.setCurrentPair(0)

	def setText(self, text):
		if text:
			self._currentLinesState = []
			lines = text.split('\\n')
			for idxLine, line in enumerate(lines):
				# line = line.rstrip()  # .split('/')'\n\r'
				if line != '':
					tline = []
					for glyphName in tdGlyphparser.translateText(self._font, line):
						if '00AD' not in glyphName:
							tline.append('%s.%s' % (glyphName, getUniqName()))
					if tline:
						self._currentLinesState.append({'line': tline,
						                                'basic': None,
						                                'idxLine': idxLine + 1,
						                                'Ypos': 0
						                                })
			self.compileLines()
			self.canvas.update()
			self.setCurrentPair(0)

	def insertGlyphsToCurrentLinesState(self, preglyphs, oldglyphs, newglyphs, postglyphs):
		finalstruct = []
		struct = self._currentLinesState

		for item in struct:
			tline = []
			for preglyph in preglyphs:
				if preglyph in item['line']:
					tline.append(preglyph)
			if tline:
				finalstruct.append({'line': tline,
				                  'basic': item['basic'],
				                  'idxLine': item['idxLine'],
				                  'Ypos': 0
				                  })

		newtxt = ' '.join(newglyphs)
		for line in newtxt.split('\n'):
			if line != '':
				tline = []
				for g in line.split(' '):
					if g != '\n' and g != '' and g in self._font:
						tline.append('%s.%s' % (g, getUniqName()))
				if tline:
					finalstruct.append({'line': tline,
					                    'basic': tline[0],
					                    'idxLine': 0,
					                    'Ypos': 0
					                    })

		saveVirtual = None
		for idx, item in enumerate(self._viewArray):
			if oldglyphs[-1] == item['nameUUID']:
				if idx + 1 < len(self._viewArray):
					if cutUniqName(oldglyphs[-1]) == self._viewArray[idx + 1]['name'] and self._viewArray[idx + 1]['virtual']:
						saveVirtual = '%s.%s' % (cutUniqName(oldglyphs[-1]), getUniqName())
		for item in struct:
			tline = []
			for postglyph in postglyphs:
				if postglyph in item['line']:
					tline.append(postglyph)
			if tline:
				if saveVirtual:
					tline.insert(0,saveVirtual)
					saveVirtual = None
				finalstruct.append({'line': tline,
				                  'basic': item['basic'],
				                  'idxLine': item['idxLine'],
				                  'Ypos': 0
				                  })

		for idx, line in enumerate(finalstruct):
			line['idxLine'] = idx+1
		self._currentLinesState = finalstruct

		selline = self._selectedLine
		self.compileLines()
		self.canvas.update()
		self._idxSelectedGlyph = self.scrollToLine(selline)
		if self._idxSelectedGlyph:
			self.setCurrentPair(self._idxSelectedGlyph)
		self._selectionCallback(self.currentPair)


	# def stepToLine (self, info):
	# 	if info['observerID'] == self.observerID:
	# 		if info['command'] == COMMAND_NEXT_LINE_SHORT:
	# 			n = self._selectedLine + 1
	# 			self.scrollToLine(n)
	# 			self.canvas.update()
	# 			# self.postMessageToKernTool(message = 'short line')
	# 		if info['command'] == COMMAND_PREV_LINE_SHORT:
	# 			n = self._selectedLine - 1
	# 			self.scrollToLine(n)
	# 			self.canvas.update()
	# 			# self.postMessageToKernTool(message = 'short line')
	# 		if info['command'] == COMMAND_NEXT_LINE:
	# 			n = self._selectedBlock + 1
	# 			self.scrollToBlock(n)
	# 			self.canvas.update()
	# 			# self.postMessageToKernTool(message = 'full line')
	# 		if info['command'] == COMMAND_PREV_LINE:
	# 			n = self._selectedBlock - 1
	# 			self.scrollToBlock(n)
	# 			self.canvas.update()
	# 			# self.postMessageToKernTool(message = 'full line')

	# def fillHashOfLine (self, idx, linenumber):
	# 	self._hashOfSelectedLine = []
	# 	for item in self._viewArray[idx:]:
	# 		if item['lineNumberOfPairs'] == linenumber:
	# 			self._hashOfSelectedLine.append(item['nameUUID'])
	# 		# else:
	# 		# 	return

	# def fillHashOfBlock (self, idx, blocknumber):
	# 	self._hashOfSelectedBlock = []
	# 	for item in self._viewArray[idx:]:
	# 		if item['blockNumberOfPairs'] == blocknumber:
	# 			self._hashOfSelectedBlock.append(item['nameUUID'])
	# 		# else:
	# 		# 	return

	def scrollToLine (self, linenumber):
		if not self._viewArray: return
		visibleWidth = self.canvas.scrollView.getNSScrollView().documentVisibleRect().size.width
		visibleHeight = self.canvas.scrollView.getNSScrollView().documentVisibleRect().size.height
		posXscroller = self.canvas.scrollView.getNSScrollView().documentVisibleRect().origin.x
		posYscroller = self.canvas.scrollView.getNSScrollView().documentVisibleRect().origin.y
		scale = self._scalefactorUI
		xpos = 0
		ypos = 0
		firstItemInLine = 0
		for idx, item in enumerate(self._viewArray):
			if item['lineNumberOfPairs'] == linenumber:
				self._positionYselected = item['y0']
				self._selectedLine = item['lineNumberOfPairs']
				self._selectedBlock = item['blockNumberOfPairs']
				firstItemInLine = idx
				# self.fillHashOfLine(idx, self._selectedLine)
				# self.fillHashOfBlock(0,self._selectedBlock)
				break
		maxY = self._viewArray[-1]['y0']
		y0 = (maxY + (-1 * self._positionYselected)) * scale
		y1 = y0 + (self._lineSize * scale)

		if y0 < posYscroller:
			ypos = y0
		elif y1 - posYscroller > visibleHeight:
			offset = visibleHeight - self._lineSize * scale
			ypos = y0 - offset  # + posYscroller
		else:
			return firstItemInLine

		point = NSPoint(xpos, ypos)
		self.canvas.scrollView.getNSScrollView().contentView().scrollToPoint_(point)
		self.canvas.scrollView.getNSScrollView().reflectScrolledClipView_(
			self.canvas.scrollView.getNSScrollView().contentView())
		return firstItemInLine

	def scrollwheel (self, event):
		# print (event)
		#
		scaleUI = self._scalefactorUI
		deltaX = event.deltaX()
		deltaY = event.deltaY()
		if deltaY == 0 and deltaX == 0: return
		if self.macos == '15':
			scaleScroll = 7#abs(deltaY)/10
		else:
			scaleScroll = 2
		# if abs(deltaY) < 3:
		# 	scaleScroll = .2
		# if abs(deltaY) > 3 and abs(deltaY) < 8:
		# 	scaleScroll = .6
		# if abs(deltaY) > 8 and abs(deltaY) < 15:
		# 	scaleScroll = 1.1
		# if abs(deltaY) > 30:
		# 	scaleScroll = 10
		visibleWidth = self.canvas.scrollView.getNSScrollView().documentVisibleRect().size.width
		visibleHeight = self.canvas.scrollView.getNSScrollView().documentVisibleRect().size.height
		posXscroller = self.canvas.scrollView.getNSScrollView().documentVisibleRect().origin.x
		posYscroller = self.canvas.scrollView.getNSScrollView().documentVisibleRect().origin.y

		xW, yW, wW, hW = self.getPosSize()
		xpoint = posXscroller - (deltaX * scaleScroll)
		ypoint = posYscroller + (deltaY * scaleScroll)
		if xpoint > self.maxXX - visibleWidth:  # - visibleWidth:
			xpoint = self.maxXX - visibleWidth  # - self.visibleWidth #- visibleWidth
		if xpoint < xW:
			xpoint = 0

		if ypoint < 0:
			ypoint = 0
		# return
		maxY = 0
		if self._viewArray:
			maxY = self._viewArray[-1]['y0']

		if posYscroller + visibleHeight - self._lineSize * scaleUI > maxY * scaleUI:
			ypoint = maxY * scaleUI - visibleHeight + self._lineSize * scaleUI
		elif posYscroller + visibleHeight - self._lineSize * scaleUI == maxY * scaleUI and deltaY > 0:
			ypoint = maxY * scaleUI - visibleHeight + self._lineSize * scaleUI

		point = NSPoint(xpoint, ypoint)
		self.canvas.scrollView.getNSScrollView().contentView().scrollToPoint_(point)
		self.canvas.scrollView.getNSScrollView().reflectScrolledClipView_(
			self.canvas.scrollView.getNSScrollView().contentView())
		if self.macos == '15':
			self.canvas.update()


	def scrollToPair (self, pairUUID):
		if not self._viewArray: return
		lid, rid = pairUUID
		visibleWidth = self.canvas.scrollView.getNSScrollView().documentVisibleRect().size.width
		visibleHeight = self.canvas.scrollView.getNSScrollView().documentVisibleRect().size.height
		posXscroller = self.canvas.scrollView.getNSScrollView().documentVisibleRect().origin.x
		posYscroller = self.canvas.scrollView.getNSScrollView().documentVisibleRect().origin.y
		scale = self._scalefactorUI
		xpos = 0
		ypos = 0

		for idx, item in enumerate(self._viewArray):
			if item['nameUUID'] == rid:
				self._positionYselected = item['y0']
				self._selectedLine = item['lineNumberOfPairs']
				self._selectedBlock = item['blockNumberOfPairs']
				# self.fillHashOfLine(idx, self._selectedLine)
				# self.fillHashOfBlock(0,self._selectedBlock)
				break

		maxY = self._viewArray[-1]['y0']
		y0 = (maxY + (-1 * self._positionYselected)) * scale
		y1 = y0 + (self._lineSize * scale)

		if y0 < posYscroller:
			ypos = y0 - visibleHeight + self._lineSize * scale
		elif y1 - posYscroller > visibleHeight:
			offset = visibleHeight - self._lineSize * scale
			ypos = y0 - offset  # + posYscroller
		else:
			return

		point = NSPoint(xpos, ypos)
		self.canvas.scrollView.getNSScrollView().contentView().scrollToPoint_(point)
		self.canvas.scrollView.getNSScrollView().reflectScrolledClipView_(
			self.canvas.scrollView.getNSScrollView().contentView())

	def scrollToBlock (self, linenumber):
		if not self._viewArray: return
		visibleWidth = self.canvas.scrollView.getNSScrollView().documentVisibleRect().size.width
		visibleHeight = self.canvas.scrollView.getNSScrollView().documentVisibleRect().size.height
		posXscroller = self.canvas.scrollView.getNSScrollView().documentVisibleRect().origin.x
		posYscroller = self.canvas.scrollView.getNSScrollView().documentVisibleRect().origin.y
		scale = self._scalefactorUI
		xpos = 0
		ypos = 0

		f1 = True
		f2 = False
		firstItemInLine = 0

		for idx, item in enumerate(self._viewArray):
			if item['blockNumberOfPairs'] == linenumber:
				self._positionYselected = item['y0']
				self._selectedLine = item['lineNumberOfPairs']
				self._selectedBlock = item['blockNumberOfPairs']
				firstItemInLine = idx
				# self.fillHashOfBlock(idx, linenumber)
				break

		maxY = self._viewArray[-1]['y0']
		y0 = (maxY + (-1 * self._positionYselected)) * scale
		y1 = y0 + (self._lineSize * scale)

		if y0 < posYscroller:
			ypos = y0 - visibleHeight + self._lineSize * scale
		elif y1 - posYscroller > visibleHeight:
			offset = visibleHeight - self._lineSize * scale
			ypos = y0 - offset  # + posYscroller
		else:
			return firstItemInLine

		point = NSPoint(xpos, ypos)
		self.canvas.scrollView.getNSScrollView().contentView().scrollToPoint_(point)
		self.canvas.scrollView.getNSScrollView().reflectScrolledClipView_(
			self.canvas.scrollView.getNSScrollView().contentView())
		return firstItemInLine

	# def getSelectedBlock (self):
	# 	result = []
	# 	for nameuuid in self._hashOfSelectedBlock:
	# 		result.append(cutUniqName(nameuuid))
	# 	return '/' + '/'.join(result)

	def getSelectedLine (self):
		selectedline = []
		if self._viewArray:
			for idx, item in enumerate(self._viewArray):
				if item['lineNumberOfPairs'] == self._selectedLine:
					selectedline.append(cutUniqName(item['nameUUID']))
		return selectedline


	def getSelectedGlyph(self):
		l, r = self.currentPair
		return r['name']


	def getSelectedLineStructured(self):
		prelines = []
		selectedline = []
		postlines = []
		idx_selected = []
		if self._viewArray:
			for idx, item in enumerate(self._viewArray):
				if item['lineNumberOfPairs'] == self._selectedLine:
					selectedline.append(item['nameUUID'])
					idx_selected.append(idx)
			for item in self._viewArray[:idx_selected[0]]:
				if not item['virtual']:
					prelines.append(item['nameUUID'])
			for item in self._viewArray[idx_selected[-1]+1:]:
				if not item['virtual']:
					postlines.append(item['nameUUID'])

		text = ''
		for g in selectedline:
			text+='/'+cutUniqName(g)
		return {'prelines': prelines,
		        'selectedline': selectedline,
		        'postlines': postlines,
		        'text': text
		        }


	def refreshKernView (self, info):
		if info['observerID'] == self.observerID:
			self.compileLines(mode = 'refresh')  # (mode='refresh')
			self.canvas.update()
			if self.currentPair:
				self._selectionCallback(self.currentPair)

	def refreshKernViewFromOtherObserver (self, info):
		if info['observerID'] != self.observerID and info['fontID'] == getFontID(self._font):
			self.compileLines(mode = 'refresh')  # (mode='refresh')
			self.canvas.update()
			if self.currentPair:
				self._selectionCallback(self.currentPair)

	# def refreshKernViewFromLinked (self, info):
	# 	if info['observerID'] == self.observerID:
	# 		# print 'getting New kern value from linked Tool'
	# 		if info['currentPair']:
	# 			if info['value']:
	# 				self._font.kerning[info['currentPair']] = info['value']
	# 			else:
	# 				self._font.kerning.remove(info['currentPair'])
	#
	# 		self.compileLines(mode = 'refresh')  # (mode='refresh')
	# 		self.canvas.update()
	# 		if self.currentPair:
	# 			self._selectionCallback(self.currentPair)

	# def postMessageToKernTool (self, message=None):
	# 	glyphsLine = []
	# 	if message == 'full line':
	# 		glyphsLine = self.getSelectedBlock()
	# 	elif message == 'short line':
	# 		glyphsLine = self.getSelectedLine()
	# 	elif message == None:
	# 		return
	# 	postEvent('typedev.KernTool.setGlyphsLine',
	# 	          glyphsLine = glyphsLine,
	# 	          fontID = getFontID(self._font),
	# 	          observerID = self.observerID)

	# def sendObserverID (self, info):
	# 	postEvent(EVENT_OBSERVERID_CALLBACK, observerID = self.observerID, fontID = getFontID(self._font))

	def mouseDown (self, event):
		visibleHeight = self.canvas.scrollView.getNSScrollView().documentVisibleRect().size.height
		# ruller_compensation = self._selfHeight - visibleHeight
		visibleWidth = self.canvas.scrollView.getNSScrollView().documentVisibleRect().size.width
		Y_local_pos = self.canvas.scrollView.getNSScrollView().documentVisibleRect().origin.y
		# X_window_pos = event.locationInWindow().x
		# Y_window_pos = event.locationInWindow().y
		Y_min_window = Y_local_pos
		Y_max_window = Y_local_pos + visibleHeight

		X_window_pos = event.locationInWindow().x
		Y_window_pos = event.locationInWindow().y
		X_local_pos = self.canvas.scrollView.getNSScrollView().documentVisibleRect().origin.x
		Y_local_pos = self.canvas.scrollView.getNSScrollView().documentVisibleRect().origin.y
		xW, yW, x2W, y2W = self.getPosSize()

		x = X_window_pos + X_local_pos  # - self._letterStep
		y = Y_window_pos + y2W + Y_local_pos

		maxY = 0
		if self._viewArray:
			maxY = self._viewArray[-1]['y0']  # + self.Ygap

		scalefactor = self._scalefactorUI
		if (maxY + 500) * scalefactor < visibleHeight:
			maxY = (visibleHeight / scalefactor) - self._lineSize  # + self.Ygap

		for idx, item in enumerate(self._viewArray):
			x0 = item['x0'] * self._scalefactorUI
			x1 = (item['x1'] + self.shiftX) * self._scalefactorUI
			# y0 = item['yV'] * self._scalefactorUI
			y0 = (maxY + (-1 * item['y0'])) * self._scalefactorUI
			y1 = y0 + ((self._lineSize) * self._scalefactorUI)  # - self.Ygap * self._scalefactorUI
			if (x0 < x and x < x1) and (y0 < y and y < y1):
				if idx == 0:
					self.setCurrentPair(idx)
				elif idx > 0:
					if item['y0'] == self._viewArray[idx - 1]['y0']:
						self.setCurrentPair(idx - 1)
					else:
						self.setCurrentPair(idx)

				if event.clickCount() == 2:
					if decodeModifiers(event.modifierFlags()) == 'Alt':
						self._commandCallback(COMMAND_OPEN_GLYPH)
					else:
						self._commandCallback(COMMAND_OPEN_LINE_IN_SPACECENTER)

				self.canvas.update()
				break

	def zoomIn (self):
		(pairL, pairR) = self.currentPair

		scale = self._scalefactorUI * self.scaleStep
		if scale < .3:
			self._scalefactorUI = scale
			self.setSize(self._scalefactorUI)
			# self.scrollToBlock(self._selectedBlock)
			if not pairR['nameUUID']:
				self.scrollToBlock(self._selectedBlock)
			else:
				self.scrollToPair((None, pairR['nameUUID']))

	def zoomOut (self):
		(pairL, pairR) = self.currentPair

		scale = self._scalefactorUI / self.scaleStep
		if scale < .035:
			self.lightmode = False
			self.lightModeSwitch()
		if scale > .013:
			self._scalefactorUI = scale
			self.setSize(self._scalefactorUI)
			if not pairR['nameUUID']:
				self.scrollToBlock(self._selectedBlock)
			else:
				self.scrollToPair((None, pairR['nameUUID']))

	def stepToPrevLine (self):
		n = self._selectedLine - 1
		self._idxSelectedGlyph = self.scrollToLine(n)
		self.setCurrentPair(self._idxSelectedGlyph)
		self.canvas.update()
		self._selectionCallback(self.currentPair)

	def stepToNextLine (self):
		n = self._selectedLine + 1
		self._idxSelectedGlyph = self.scrollToLine(n)
		self.setCurrentPair(self._idxSelectedGlyph)
		self.canvas.update()
		self._selectionCallback(self.currentPair)

	def stepToNextBlock (self):
		n = self._selectedBlock + 1
		self._idxSelectedGlyph = self.scrollToBlock(n)
		self.setCurrentPair(self._idxSelectedGlyph)
		self.canvas.update()
		self._selectionCallback(self.currentPair)

	def stepToPrevBlock (self):
		n = self._selectedBlock - 1
		self._idxSelectedGlyph = self.scrollToBlock(n)
		self.setCurrentPair(self._idxSelectedGlyph)
		self.canvas.update()
		self._selectionCallback(self.currentPair)

	def touchModeSwitch (self):
		self.toucheMode = not self.toucheMode
		self._window.gcontrol.ctrl1.setStateItem(self._window.controlShowTouchedID, self.toucheMode)
		self.canvas.update()

	def valuesModeSwitch (self):
		self.showInfo = not self.showInfo
		self._window.gcontrol.ctrl1.setStateItem(self._window.controlShowValuesID, self.showInfo)
		self.canvas.update()

	def lightModeSwitch (self):
		self.lightmode = not self.lightmode
		self._window.gcontrol.ctrl1.setStateItem(self._window.controlLightModeID, self.lightmode)
		self.canvas.update()

	def openFileCall (self):
		pairsfile = getFile(messageText = 'Select text file', title = 'title')
		self.loadText(filepath = pairsfile)
		self.canvas.update()

	def pairsBuilderCall (self):
		# print ('PairsMaker')
		PairsBuilderDialogWindow(parentWindow = self._window,
		                         font = self._font, kernhash = self.hashKernDic,
		                         callback = self.getPairsListFromPairsBuilderDialog,
		                         leftList = self.PB_leftList,
		                         rightList = self.PB_rightList,
		                         patternLeft = self.PB_patternLeft,
		                         patternRight = self.PB_patternRight)

	def keyDown (self, event):
		keypress = decodeCanvasKeys(event.keyCode(), event.modifierFlags())
		commands = translateKeyCodesToKernToolCommands(keypress)
		if commands['command'] == COMMAND_ZOOM_IN:
			self.zoomIn()
		if commands['command'] == COMMAND_ZOOM_OUT:
			self.zoomOut()
		if commands['command'] == COMMAND_REFRESH:
			if self._refreshCallback:
				self._refreshCallback(self._font)

		if commands['command'] == COMMAND_NEXT_LINE_SHORT:
			self.stepToNextLine()

		if commands['command'] == COMMAND_PREV_LINE_SHORT:
			self.stepToPrevLine()

		if commands['command'] == COMMAND_NEXT_LINE:
			self.stepToNextBlock()

		if commands['command'] == COMMAND_PREV_LINE:
			self.stepToPrevBlock()

		if commands['command'] == COMMAND_SWITCH_TOUCHE_MODE:
			self.touchModeSwitch()

		if commands['command'] == COMMAND_SWITCH_VALUES_MODE:
			self.valuesModeSwitch()

		if commands['command'] == COMMAND_OPEN_PAIRS_FILE:
			self.openFileCall()

		if commands['command'] == COMMAND_OPEN_PAIRS_BUILDER:
			self.pairsBuilderCall()

		if commands['command'] == COMMAND_SELECT_FONT:
			if self._commandCallback:
				self._commandCallback(COMMAND_SELECT_FONT)

		if commands['command'] == COMMAND_ENTER:
			if self._commandCallback:
				self._commandCallback(COMMAND_ENTER)
		if commands['command'] == COMMAND_ALT_ENTER:
			if self._commandCallback:
				self._commandCallback(COMMAND_ALT_ENTER)

		if commands['command'] == COMMAND_LIGHT_MODE:
			self.lightModeSwitch()

		if commands['command'] == COMMAND_DELETE_PAIR:
			self.setValue2Pair(self.currentPairForKern, operation = 'remove')
		if commands['command'] == COMMAND_SET_KERNING_DEC10:
			self.setCurrentPairValue(value = -10)
		if commands['command'] == COMMAND_SET_KERNING_DEC1:
			self.setCurrentPairValue(value = -1)
		if commands['command'] == COMMAND_SET_KERNING_DEC5:
			self.setCurrentPairValue(value = -5)
		if commands['command'] == COMMAND_SET_KERNING_INC10:
			self.setCurrentPairValue(value = 10)
		if commands['command'] == COMMAND_SET_KERNING_INC1:
			self.setCurrentPairValue(value = 1)
		if commands['command'] == COMMAND_SET_KERNING_INC5:
			self.setCurrentPairValue(value = 5)
		if commands['command'] == COMMAND_TAKE_THE_VALUE:
			self.setCurrentPairValue(value = None, multiply = commands['value'])
		if commands['command'] == COMMAND_PAIRVALUE_AUTOCALCULATE:
			pairToCalc = {}
			pairToCalc['L_nameUUID'] = self.currentPair[0]['nameUUID']
			pairToCalc['R_nameUUID'] = self.currentPair[1]['nameUUID']
			pairToCalc['kernValue'] = self.currentPair[0]['kernValue']
			deltaKern = autoCalcPairValue(self._font, self.hashKernDic, pairToCalc)
			self.setCurrentPairValue(deltaKern)

		if commands['command'] == COMMAND_MAKE_EXCEPTION:
			self.makeException()

		if commands['command'] == COMMAND_FLIP_PAIR:
			self.flipPair()

		if commands['command'] == COMMAND_NEXT_PAIR:
			self.nextPair()
		if commands['command'] == COMMAND_PREV_PAIR:
			self.prevPair()

		if commands['command'] == COMMAND_OFF_KERN:
			self.offKerning()

		if commands['command'] == COMMAND_COPYKERN:
			self.copyKerningValue()
		if commands['command'] == COMMAND_PASTEKERN:
			self.pasteKerningValue()

	def offKerning(self):
		self.showKerning = not self.showKerning
		self.compileLines(mode = 'refresh')
		self._window.gcontrol.ctrl1.setStateItem(self._window.controlOffKerningID, not self.showKerning)
		self.canvas.update()

	def copyKerningValue(self):
		if self.currentPairForKern in self._font.kerning:
			self._kernValueCopy = self._font.kerning[self.currentPairForKern]
			# print('value copyied', self._kernValueCopy)
		else:
			self._kernValueCopy = None

	def pasteKerningValue(self):
		# print ('trying to paste value', self._kernValueCopy, 'to', self.currentPairForKern)
		self.setValue2Pair(self.currentPairForKern, value = self._kernValueCopy, operation = 'value')


	def makeException (self):
		l = self.currentPair[0]['nameUUID']
		r = self.currentPair[1]['nameUUID']

		pair = researchPair(self._font, self.hashKernDic, (l, r))
		lGG = pair['L_inGroup']
		rGG = pair['R_inGroup']
		gL = pair['L_nameForKern']
		gR = pair['R_nameForKern']

		if lGG and rGG:
			if l and r:
				TDExceptionView(self._window, font = self._font, hashKernDic = self.hashKernDic,
				                pair = (cutUniqName(l), cutUniqName(r)),
				                callback = self.getResultFormExceptionWindow2,
				                autokern = self.useAutoKern)

		elif (not lGG) and (not rGG): pass
		else:
			kernValue = self._font.kerning[(cutUniqName(gL), cutUniqName(gR))]
			if kernValue != None:
				# print 'Making exception' , cutUniqName(l), cutUniqName(r) , kernValue
				self.setValue2Pair(pair = (cutUniqName(l), cutUniqName(r)), value = kernValue)
			else:
				# print 'Making exception Zero' , cutUniqName(l), cutUniqName(r) , 0
				self.setValue2Pair(pair = (cutUniqName(l), cutUniqName(r)), value = 0, operation = 'exception')
		selline = self._selectedLine
		selidx = self._idxSelectedGlyph
		self.compileLines(mode = 'refresh')
		# self.scrollToLine(selline)
		self.setCurrentPair(selidx)
		self.canvas.update()
		# self._selectionCallback(self.currentPair)

	def getResultFormExceptionWindow2 (self, result):
		if result:
			(ex_l, ex_r), deltakern, autokern = result
			self.useAutoKern = autokern
			if not deltakern:
				deltakern = 0
			gL = self.currentPair[0]['L_nameForKern']
			gR = self.currentPair[0]['R_nameForKern']
			if (cutUniqName(gL), cutUniqName(gR)) in self._font.kerning:
				kernValue = self._font.kerning[(cutUniqName(gL), cutUniqName(gR))]
			else:
				kernValue = None
			if kernValue != None:
				# print 'Making Exception with initial kernValue', kernValue
				self.setValue2Pair(pair = (ex_l, ex_r), value = kernValue + deltakern)
			else:
				# print 'Making Exception with Zero kernValue', kernValue
				self.setValue2Pair(pair = (ex_l, ex_r), value = deltakern, operation = 'exception')

		selline = self._selectedLine
		selidx = self._idxSelectedGlyph
		self.compileLines(mode = 'refresh')
		# self.scrollToLine(selline)
		self.setCurrentPair(selidx)
		self.canvas.update()
		# self._selectionCallback(self.currentPair)

	def nextPair (self):
		step = 1
		if self._viewArray:
			self._idxSelectedGlyph += step
			if self._idxSelectedGlyph >= len(self._viewArray) - 1:
				self._idxSelectedGlyph -= step
			else:
				if self._viewArray[self._idxSelectedGlyph]['lineNumberOfPairs'] != \
						self._viewArray[self._idxSelectedGlyph + 1]['lineNumberOfPairs']:
					self._idxSelectedGlyph += step
			self.setCurrentPair(self._idxSelectedGlyph)
			self.canvas.update()

	def prevPair (self):
		if self._viewArray:
			self._idxSelectedGlyph -= 1
			if self._idxSelectedGlyph <= 0:
				self._idxSelectedGlyph = 0
			else:
				if self._viewArray[self._idxSelectedGlyph]['lineNumberOfPairs'] != \
						self._viewArray[self._idxSelectedGlyph + 1]['lineNumberOfPairs']:
					self._idxSelectedGlyph -= 1
			self.setCurrentPair(self._idxSelectedGlyph)
			self.canvas.update()

	# def findOverlapingGlyphs (self):
	# 	line = ''
	#
	# 	for glyph_left in self._font.selection:
	# 		for glyph_right in self._font.selection:
	# 			pairinfo = researchPair(self._font, self.hashKernDic, (glyph_left, glyph_right))
	# 			kernValue = pairinfo['kernValue']
	# 			if kernValue == None:
	# 				kernValue = 0
	#
	# 			if checkOverlapingGlyphs(self._font[glyph_left], self._font[glyph_right], kernvalue = kernValue):
	# 				line += '/%s/%s ' % (glyph_left, glyph_right)
	#
	# 	self.setGlyphs(notification = {'glyphsLine': line})

	def flipPair (self):
		(pairL, pairR) = self.currentPair
		for idx, item in enumerate(self._currentLinesState):
			if pairR['nameUUID'] in item['line']:
				for lidx, lineitem in enumerate(item['line']):
					if lineitem == pairR['nameUUID']:
						item['line'][lidx - 1] = cutUniqName(pairR['nameUUID']) + '.' + getUniqName()
						item['line'][lidx] = cutUniqName(pairL['nameUUID']) + '.' + getUniqName()
		selline = self._selectedLine
		selidx = self._idxSelectedGlyph
		self.compileLines() # mode = 'refreshline', line2refresh = selline
		self.scrollToLine(selline)
		self.setCurrentPair(selidx)
		self.canvas.update()
		self._selectionCallback(self.currentPair)

	def switchPair (self, pair):
		(pairL, pairR) = self.currentPair
		swchL, swchR = pair
		for idx, item in enumerate(self._currentLinesState):
			if pairR['nameUUID'] in item['line']:
				for lidx, lineitem in enumerate(item['line']):
					if lineitem == pairR['nameUUID']:
						item['line'][lidx - 1] = swchL + '.' + getUniqName()
						item['line'][lidx] = swchR + '.' + getUniqName()
		selline = self._selectedLine
		selidx = self._idxSelectedGlyph
		self.compileLines() # mode = 'refreshline', line2refresh = selline
		self.scrollToLine(selline)
		self.setCurrentPair(selidx)
		self.canvas.update()
		self._selectionCallback(self.currentPair)

	def setCurrentPair (self, idx):
		if not self._viewArray: return
		# print 'setCurrentPair'
		self._selectedLine = self._viewArray[idx]['lineNumberOfPairs']
		self._selectedBlock = self._viewArray[idx]['blockNumberOfPairs']
		self._idxSelectedGlyph = idx
		self.currentPair = (self._viewArray[idx], self._viewArray[idx + 1])
		pair = researchPair(self._font, self.hashKernDic,
		                    (self._viewArray[idx]['nameUUID'], self._viewArray[idx + 1]['nameUUID']))
		self.currentPairForKern = (pair['L_realName'], pair['R_realName'])
		self.scrollToLine(self._selectedLine)
		self._selectionCallback(self.currentPair)
		if pair['kernValue']:
			self._window.ctrl2.setLabelValue(self._window.labelCurrentPairID,
		                                 '%s  %s  %s' % (getDisplayNameGroup(self.currentPairForKern[0]), getDisplayNameGroup(self.currentPairForKern[1]), str(pair['kernValue'])))
		else:
			self._window.ctrl2.setLabelValue(self._window.labelCurrentPairID,
			                                 '%s  %s' % (getDisplayNameGroup(self.currentPairForKern[0]), getDisplayNameGroup(self.currentPairForKern[1])))
		# for item in self._viewArray:
		# 	if self._selectedLine == item['lineNumberOfPairs']:
		# 		for a, v in item.items():
		# 			print a, v
		# print 'SELECTION ====='
		# print self.currentPair[0]
		# print self.currentPair[1]
		# print self.currentPairForKern

	def findFirstPair(self, pair):
		l, r = pair
		for idx, item in enumerate(self._viewArray):
			if idx < len(self._viewArray)+1:
				if item['name'] == l and self._viewArray[idx+1]['name'] == r:
					self.setCurrentPair(idx)

	def setValue2Pair (self, pair, value=None, operation='value'):
		if not self.showKerning: return
		if operation == 'value':
			(pairL, pairR) = self.currentPair
			if not value and not pairL['exception'] and pair in self._font.kerning:
				self._font.kerning.remove(pair)
			else:
				self._font.kerning[pair] = value
		elif operation == 'remove':
			if pair in self._font.kerning:
				self._font.kerning.remove(pair)
		elif operation == 'exception':
			if not value:
				value = 0
			self._font.kerning[pair] = value

		self.compileLines(mode = 'refresh')  # (mode='refresh')
		# self.setCurrentPair(self._idxSelectedGlyph)
		# postEvent(EVENT_REFRESH_KERNTOOL, info = None)
		postEvent(EVENT_REFRESH_ALL_OBSERVERS,
		          fontID = self.fontID, #getFontID(self._font),
		          observerID = self.observerID,
		          pair = pair)
		self.setCurrentPair(self._idxSelectedGlyph)
		self.canvas.update()
		# if self.currentPair:
		# 	self._selectionCallback(self.currentPair)

	def setCurrentPairValue (self, value, multiply=None):
		if self.currentPairForKern:
			if value:
				self.lastValue = value
				self.lastMultiply = []
			elif multiply != None:
				if multiply == 0:
					multiply = 10
				value = (self.lastValue * multiply) - self.lastValue  # simple way, one multiply
			if self.currentPairForKern in self._font.kerning and kern(self._font.kerning[self.currentPairForKern]):  # != None:
				self.setValue2Pair(pair = self.currentPairForKern,
				                   value = self._font.kerning[self.currentPairForKern] + value)
			else:
				self.setValue2Pair(pair = self.currentPairForKern, value = value)
			(pair, pair2) = self.currentPair
			if self.currentPairForKern in self._font.kerning and (self._font.kerning[self.currentPairForKern]) == 0 and (not pair['exception']):
				self.setValue2Pair(pair = self.currentPairForKern, operation = 'remove')


	def compileLines (self, mode='rebuild', pair2refresh = None, line2refresh = None):  # mode = 'refresh'
		if not self._font:
			self.setFont(CurrentFont(), hashKernDic = TDHashKernDic(CurrentFont()))

		visibleWidth = self.visibleWidth
		if mode == 'rebuild':
			self._viewArray = []
			self._hashOfPairs = {}
			self.maxX = 0
			scale = self._scalefactorUI
			lineStep = self._lineSize
			shiftX = self.shiftX
			Xshift = 50
			Xpos = shiftX
			Ypos = 0
			carret = 0
			smartmode = True
			self.lineCount = 0
			virtShift = 0
			widthvirt = 0
			kernValuevirt = 0
			idxLine = 0
			maxY = 0

			scalefactor = self._scalefactorUI
			for item in self._currentLinesState:
				line = item['line']
				leftglyph = item['basic']
				idxLine = item['idxLine']

				self._pairsToDisplay = getListOfPairsToDisplay(self._font, self.hashKernDic, line)
				for idx, glyphnameUUID in enumerate(line):
					kernValue = 0
					exception = False
					if self._pairsToDisplay and (idx < len(self._pairsToDisplay)):
						pair = self._pairsToDisplay[idx]
						kernValue = pair['kernValue']
						exception = pair['exception']

					realname = cutUniqName(glyphnameUUID)
					glyph = self._font[realname]
					nameToDisplay = realname
					if not kernValue:
						kernValue = 0

					width = glyph.width
					if (kernValue + carret + width + shiftX + widthvirt + kernValuevirt) * scale > visibleWidth - (
							shiftX * scale) - (Xshift * scale):
						Ypos += lineStep
						Xpos = shiftX
						if smartmode:
							glyphnameUUIDvirt = line[idx - 1]
							widthvirt = self._font[cutUniqName(glyphnameUUIDvirt)].width
							wlast = widthvirt
							kernValuevirt = 0
							exceptionvirt = False
							if self._pairsToDisplay:
								try:
									pairvirt = self._pairsToDisplay[idx - 1]
									kernValuevirt = pairvirt['kernValue']
									exceptionvirt = pairvirt['exception']
								except:
									kernValuevirt = 0
									exceptionvirt = False
								if not kernValuevirt:
									kernValuevirt = 0
							self._viewArray.append({'name': cutUniqName(glyphnameUUIDvirt),
							                        'nameUUID': cutUniqName(glyphnameUUIDvirt) + '.' + getUniqName(),
							                        'basic': leftglyph,
							                        'width': widthvirt,
							                        'kernValue': pairvirt['kernValue'],
							                        'exception': exceptionvirt,
							                        'x0': Xpos,
							                        'x1': kernValuevirt + Xpos + widthvirt,
							                        'y0': Ypos,
							                        'yV': Ypos,
							                        'blockNumberOfPairs': idxLine,
							                        'lineNumberOfPairs': self.lineCount + 1,
							                        'virtual': True,
							                        'L_inGroup': pair['L_inGroup'],
							                        'R_inGroup': pair['R_inGroup'],
							                        'L_nameForKern': pair['L_nameForKern'],
							                        'R_nameForKern': pair['R_nameForKern'],
							                        # 'L_markException': pair['L_markException'],
							                        # 'R_markException': pair['R_markException']
							                        })
							Xpos += kernValuevirt + widthvirt
							self._viewArray.append({'name': cutUniqName(glyphnameUUID),
							                        'nameUUID': glyphnameUUID,
							                        'basic': leftglyph,
							                        'width': width,
							                        'kernValue': pair['kernValue'],
							                        'exception': exception,
							                        'x0': Xpos,
							                        'x1': kernValue + Xpos + width,
							                        'y0': Ypos,
							                        'yV': Ypos,
							                        'blockNumberOfPairs': idxLine,
							                        'lineNumberOfPairs': self.lineCount + 1,
							                        'virtual': False,
							                        'L_inGroup': pair['L_inGroup'],
							                        'R_inGroup': pair['R_inGroup'],
							                        'L_nameForKern': pair['L_nameForKern'],
							                        'R_nameForKern': pair['R_nameForKern'],
							                        # 'L_markException': pair['L_markException'],
							                        # 'R_markException': pair['R_markException']
							                        })
							virtShift = kernValue + Xpos + width
						else:
							self._viewArray.append({'name': cutUniqName(glyphnameUUID),
							                        'nameUUID': glyphnameUUID,
							                        'basic': leftglyph,
							                        'width': width,
							                        'kernValue': pair['kernValue'],
							                        'exception': exception,
							                        'x0': Xpos,
							                        'x1': kernValue + Xpos + width,
							                        'y0': Ypos,
							                        'yV': Ypos,
							                        'blockNumberOfPairs': idxLine,
							                        'lineNumberOfPairs': self.lineCount - 1,
							                        'virtual': False,
							                        'L_inGroup': pair['L_inGroup'],
							                        'R_inGroup': pair['R_inGroup'],
							                        'L_nameForKern': pair['L_nameForKern'],
							                        'R_nameForKern': pair['R_nameForKern'],
							                        # 'L_markException': pair['L_markException'],
							                        # 'R_markException': pair['R_markException']
							                        })
						carret = shiftX
						self.lineCount += 1
					else:
						virtShift = 0
						self._viewArray.append({'name': cutUniqName(glyphnameUUID),
						                        'nameUUID': glyphnameUUID,
						                        'basic': leftglyph,
						                        'width': width,
						                        'kernValue': pair['kernValue'],
						                        'exception': exception,
						                        'x0': Xpos,
						                        'x1': kernValue + Xpos + width,
						                        'y0': Ypos,
						                        'yV': Ypos,
						                        'blockNumberOfPairs': idxLine,
						                        'lineNumberOfPairs': self.lineCount,
						                        'virtual': False,
						                        'L_inGroup': pair['L_inGroup'],
						                        'R_inGroup': pair['R_inGroup'],
						                        'L_nameForKern': pair['L_nameForKern'],
						                        'R_nameForKern': pair['R_nameForKern'],
						                        # 'L_markException': pair['L_markException'],
						                        # 'R_markException': pair['R_markException']
						                        })
					Xpos += kernValue + width
					carret += kernValue + width

				# END of Block pairs
				carret = shiftX
				Ypos += lineStep
				Xpos = shiftX
				self.lineCount += 1

			self.recalculateFrame(visibleWidth)

		if mode == 'refresh' and not self.highLevelLoaded and not self.macos=='15':
			if self._viewArray:
				self.maxX = 0
				for idx, item in enumerate(self._viewArray):
					if idx < len(self._viewArray) and idx > 0:
						if self._viewArray[idx - 1]['y0'] == self._viewArray[idx]['y0']:
							litem = self._viewArray[idx - 1]['name']
							ritem = self._viewArray[idx]['name']
							lglyphwidth = self._font[litem].width
							pairRL = researchPair(self._font, self.hashKernDic, (litem, ritem))
							if self.showKerning:
								if pairRL['kernValue'] == None:
									kV = 0
								else:
									kV = pairRL['kernValue']
							else:
								kV = 0
								pairRL['kernValue'] = None
								pairRL['exception'] = False
							x1 = self._viewArray[idx - 1]['x0'] + lglyphwidth + kV
							self._viewArray[idx]['x0'] = x1
							self._viewArray[idx - 1]['kernValue'] = pairRL['kernValue']
							self._viewArray[idx - 1]['exception'] = pairRL['exception']
							self._viewArray[idx - 1]['x1'] = x1
							# self._viewArray[idx - 1]['L_markException'] = pairRL['L_markException']
							# self._viewArray[idx - 1]['R_markException'] = pairRL['R_markException']
		if mode == 'refreshline':
			print ('refreshline not working yet')

		if self._font:
			self._window.ctrl2.setLabelValue(self._window.labelTotalPairsID, len(self._font.kerning))
			# self._window.ctrl2.setLabelValue(self._window.labelTotalGroupsID, len(self._font.groups))

			if len(self._viewArray) - self.lineCount > 4000:
				self.highLevelLoaded = True
				self._window.ctrl2.setLabelValue(self._window.labelViewPairsID,
				                                 str(len(self._viewArray) - self.lineCount), color = COLOR_KERN_VALUE_NEGATIVE )
			else:
				self.highLevelLoaded = False
				self._window.ctrl2.setLabelValue(self._window.labelViewPairsID,
				                                 str(len(self._viewArray) - self.lineCount))
			# self._window.ctrl2.setLabelValue(self._window.labelVersion, KERNTOOL_VERSION + ':' +self.observerID.replace('uu','') )

	def recalculateFrame (self, canvaswidth=None):
		scalefactor = self._scalefactorUI
		if canvaswidth:
			visibleWidth = canvaswidth
		else:
			visibleWidth = self.canvas.scrollView.getNSScrollView().documentVisibleRect().size.width
		self.visibleWidth = visibleWidth
		visibleHeight = self.canvas.scrollView.getNSScrollView().documentVisibleRect().size.height
		yoff = (self.lineCount * self._lineSize) * scalefactor  # + self.Ygap*2
		if yoff < visibleHeight:
			yoff = visibleHeight  # + 500
		self.canvas._view.setFrame_(NSMakeRect(0, 0, visibleWidth + 60, yoff))
		self.maxXX = visibleWidth + 60

	def draw (self):
		# self.recalculateFrame(self.visibleWidth)
		self._viewFontName = 'Menlo'#'.SFCompactText-Regular'
		self._viewFontSize = 80
		font(self._viewFontName, fontSize = self._viewFontSize)
		stroke(0, 0, 0, 0)
		strokeWidth(0)

		def drawException (x, y):
			s = 15
			newPath()
			moveTo((x + s * 4, y + s * 8))
			lineTo((x + s * 1, y + s * 3))
			lineTo((x + s * 4, y + s * 3))
			lineTo((x + s * 4, y + s * 0))
			lineTo((x + s * 7, y + s * 5))
			lineTo((x + s * 4, y + s * 5))
			closePath()
			drawPath()

		def drawSelectionCursor (x, y, color, markException=False):
			opt = 0
			if markException:
				opt = 20
			hw = 70 + opt
			x = x - hw
			fillRGB(color)
			newPath()
			moveTo((x, y))
			lineTo((x + hw, y + hw + hw/4 - opt))
			lineTo((x + hw * 2, y))
			closePath()
			drawPath()
			if markException:

				fill(1)
				if self.darkmodeWarm:
					fillRGB((.75, .73, .7, 1))
				oh = 80
				oval(x+(hw*2-oh)/2, y-oh/2 + 20, oh, oh)
				fillRGB(COLOR_KERN_VALUE_NEGATIVE)
				oh = 55
				oval(x + (hw * 2 - oh) / 2, y - oh / 2 +20, oh, oh)

		visibleWidth = self.visibleWidth
		visibleHeight = self.canvas.scrollView.getNSScrollView().documentVisibleRect().size.height

		Y_local_pos = self.canvas.scrollView.getNSScrollView().documentVisibleRect().origin.y
		X_local_pos = self.canvas.scrollView.getNSScrollView().documentVisibleRect().origin.x

		Y_min_window = Y_local_pos
		Y_max_window = Y_local_pos + visibleHeight

		X_min_window = X_local_pos
		X_max_window = X_local_pos + visibleWidth

		scalefactor = self._scalefactorUI
		shiftX = self.shiftX
		Ygap = self.Ygap

		yoff = ((self.lineCount - 1) * self._lineSize)  # + Ygap/scalefactor
		if self._viewArray:
			maxY = self._viewArray[-1]['y0']
		else:
			return

		if self.darkmodeWarm:
			fillRGB((.75, .73, .7, .8))
			_ry = maxY
			# print('maxY', maxY)
			if maxY < visibleHeight:
				_ry = visibleHeight + 500
			rect(0, 0, visibleWidth/scalefactor + 60, _ry)

		scale(scalefactor)
		stroke(0, 0, 0, 0)
		strokeWidth(0)

		if (maxY + 500) * scalefactor < visibleHeight:
			translate(shiftX, (visibleHeight / scalefactor) - self._lineSize + 500)
		else:
			translate(shiftX, maxY + 500)

		# Lets start..
		for idx, item in enumerate(self._viewArray):
			Xpos = item['x0']
			Ypos = item['y0']

			# DRAW _only_ if it visible in window frame
			if (Y_min_window - self._lineSize * scalefactor < ((maxY + (-1 * Ypos)) * scalefactor)
			    and Y_max_window > ((maxY + (-1 * Ypos)) * scalefactor)) \
					and ((X_min_window * scalefactor < Xpos * scalefactor)
					     and (X_max_window > Xpos * scalefactor)):

				if self.highLevelLoaded or self.macos=='15': # Refresh kerning values and calc lines when drawing loop #experimental
					if idx < len(self._viewArray)-1 and idx > 0:
						if self._viewArray[idx]['y0'] == self._viewArray[idx+1]['y0']:
							litem = self._viewArray[idx]['name']
							ritem = self._viewArray[idx+1]['name']
							lglyphwidth = self._font[litem].width
							pairRL = researchPair(self._font, self.hashKernDic, (litem, ritem))
							if self.showKerning:
								if pairRL['kernValue'] == None:
									kV = 0
								else:
									kV = pairRL['kernValue']
							else:
								kV = 0
								pairRL['kernValue'] = None
								pairRL['exception'] = False
							x1 = self._viewArray[idx]['x0'] + lglyphwidth + kV
							self._viewArray[idx+1]['x0'] = x1
							self._viewArray[idx]['kernValue'] = pairRL['kernValue']
							self._viewArray[idx]['exception'] = pairRL['exception']
							self._viewArray[idx]['x1'] = x1
							Xpos = item['x0']
							Ypos = item['y0']


				# DRAW Selection bars
				if not self.lightmode and self.showSelectionBars:
					widthSelector = 100  # (shiftX / 3) * 2
					if (item['blockNumberOfPairs'] == self._selectedBlock):
						fillRGB(COLOR_GREY_50)
						rect(-1 * shiftX, -1 * Ypos - 500, widthSelector, self._lineSize)
					if (item['lineNumberOfPairs'] == self._selectedLine):
						fillRGB(COLOR_BLACK)
						rect(-1 * shiftX, -1 * Ypos - 490, widthSelector, self._lineSize)
						fillRGB(COLOR_GREY_10)

						if self.darkmodeWarm:
							fillRGB(COLOR_GREY_50)
						rect(-1 * shiftX, -1 * Ypos - 500 ,   (visibleWidth + 60) / scalefactor, 1 / scalefactor)
						# if item['y0'] == self._viewArray[idx + 1]['y0']:
						# 	fillRGB((.5,.5,.5,.5))
						# 	rect(-1 * shiftX, -1 * Ypos - 500, (visibleWidth + 60) / scalefactor, self._lineSize)
						# fillRGB(COLOR_GREY_50)
						# rect(-1 * shiftX,  -1 * Ypos + self._lineSize - 500 + 5, 300, 5) # -1 *

				save()
				fillRGB(COLOR_BLACK)

				# DRAW Glyphs and check overlaping
				if self.toucheMode and not self.lightmode:
					if self.touchFlag:
						fillRGB(COLOR_KERN_VALUE_NEGATIVE)
						self.touchFlag = False
					if idx + 1 < len(self._viewArray):
						if item['y0'] == self._viewArray[idx + 1]['y0']:
							kernValue = item['kernValue']
							if kernValue == None: kernValue = 0
							currGlyph = self._font[item['name']]
							nextGlyph = self._font[self._viewArray[idx + 1]['name']]
							if checkOverlapingGlyphs(self._font, currGlyph, nextGlyph, kernValue):
								fillRGB(COLOR_KERN_VALUE_NEGATIVE)
								self.touchFlag = True

				glyph = self._font[item['name']]
				pen = CocoaPen(self._font)
				translate(Xpos, -1 * Ypos + 50)
				item['yV'] = yoff - Ypos  # - Ygap
				glyph.draw(pen)
				drawPath(pen.path)
				restore()

				nextItemVirtual = False
				HVcontrol = 60
				Vcontrol = 80
				HVkern = 60
				Ycontrol = -400

				xK = 0
				save()
				translate(0, -1 * Ypos)
				if idx + 1 < len(self._viewArray):
					nextItemVirtual = self._viewArray[idx + 1]['virtual']

				# DRAW kerning value
				if not nextItemVirtual and not self.lightmode and (idx + 1 < len(self._viewArray)) and self._viewArray[idx + 1]['lineNumberOfPairs'] == self._viewArray[idx]['lineNumberOfPairs']:
					if item['kernValue'] != None:
						kV = item['kernValue']
						if kV in range(1, 60):
							kV = 60
						if kV in range(-60, 0):
							kV = -60
						xK = item['x0'] + item['width']
						if kV > 0:
							xK = item['x0'] + item['width']
							fillRGB(COLOR_KERN_VALUE_POSITIVE)
							rect(xK, Ycontrol + HVcontrol, abs(kV), HVkern)
						elif kV < 0:
							xK = item['x1']
							fillRGB(COLOR_KERN_VALUE_NEGATIVE)
							rect(xK, Ycontrol + HVcontrol, abs(kV), HVkern)
						elif kV == 0:
							xK = item['x0'] + item['width']
							kV = 60
							fillRGB(COLOR_KERN_VALUE_NEGATIVE)

						if item['exception']:
							drawException(xK + abs(kV) / 2 - HVcontrol, Ycontrol - HVcontrol)
						if self.valuesMode:
							text(str(item['kernValue']), (xK + abs(kV) + 20, Ycontrol - 40 )) #HVcontrol))

				# DRAW margins
				if self.showInfo and not self.lightmode:
					xlM = item['x0']
					xrM = item['x0'] + item['width']
					t1 = Ycontrol + 175 #+ 1200
					t2 = HVcontrol
					wbar = 150
					lbar = 5
					gapbar = 30
					lM = 0
					rM = 0
					if self._font.info.italicAngle == 0 or not self._font.info.italicAngle:
						if glyph.leftMargin:
							lM = int(round(glyph.leftMargin,0))
						if glyph.rightMargin:
							rM = int(round(glyph.rightMargin,0))
					else:
						if glyph.angledLeftMargin:
							lM = int(round(glyph.angledLeftMargin,0))
						if glyph.angledRightMargin:
							rM = int(round(glyph.angledRightMargin,0))

					fill(.5)
					if self.darkmodeWarm:
						fill(.3,.3,.3,1)
					# leftMargin mark
					rect(xlM, t1+10, lbar, t2) # vbar
					rect(xlM, t1 + t2 - lbar +10, wbar, lbar) # hbar
					text(str(lM), (xlM + 30, t1 - 40 +10))

					# rightMargin mark
					rect(xrM-wbar, t1 + t2 -lbar + gapbar, wbar, lbar) # hbar
					rect(xrM-lbar, t1 + t2 -lbar + gapbar, lbar, t2+lbar) # vbar
					rm = str(rM)
					# rmoff = len(rm)*40 + 45
					nx, ny = textSize(rm)
					text(rm,(xrM - nx - 30, t1 + gapbar + 60 ))

					rect(xlM + item['width']/2-lbar/2, Ycontrol - 100 + lbar, lbar, t2)
					if (item['lineNumberOfPairs'] != self._selectedLine):
						rect(xlM + item['width']/2-lbar/2 - wbar/2, Ycontrol - 100, wbar, lbar)

				# DRAW cursor selected pair
				if self.currentPair and not self.lightmode:
					l, r = self.currentPair
					cursorcolor = COLOR_L_GROUP_ICON

					# check language compatibility (experimental)
					# langComp = self.langSet.checkPairLanguageCompatibility(self._font, (l['name'], r['name']))
					# if not langComp:
					# 	cursorcolor = COLOR_KERN_VALUE_NEGATIVE

					if (item['nameUUID'] == l['nameUUID']):
						markException = False
						if item['exception'] and item['L_nameForKern'] != self.currentPairForKern[0]:
							markException = True
						drawSelectionCursor(item['x0'] + item['width'] / 2, Ycontrol + HVcontrol , cursorcolor, markException = markException) #
					if (item['nameUUID'] == r['nameUUID']):
						markException = False
						if self._viewArray[idx-1]['exception'] and self._viewArray[idx-1]['R_nameForKern'] != self.currentPairForKern[1]:
							markException = True
						drawSelectionCursor(item['x0'] + item['width'] / 2, Ycontrol + HVcontrol, cursorcolor, markException = markException)

				restore()

# ===================================================================================================
class EditLineDialog(object):
	# nsViewClass = NSView
	def __init__ (self, parentWindow, font=None, callback = None):
		wW = 750
		hW = 180
		self.w = Sheet((wW, hW), parentWindow, minSize = (wW,hW), maxSize = (wW,1000))
		self.callback = callback
		self.font = font
		self.textMode = 1

		segmentsGrp = [ {'width': 66, 'title': 'All'},
						{'width': 66, 'title': 'Block'},
		                {'width': 66, 'title': 'Line'} ]
		self.w.btnBlockLineSwitch = SegmentedButton((5, 5, 205, 17),
		                                               segmentDescriptions = segmentsGrp,
		                                               selectionStyle = 'one',
		                                               sizeStyle = 'small',
		                                               # callback = self.btnPairsPerLineCallback)
		                                               )
		self.w.btnBlockLineSwitch.set(2)
		self.w.btnBlockLineSwitch.enable(False)

		segmentsGrp = [{'width': 100, 'title': 'Text'},
		               {'width': 100, 'title': 'Glyph names'}]
		self.w.btnTextRepresentation = SegmentedButton((-208, 5, 205, 17),
		                                         segmentDescriptions = segmentsGrp,
		                                         selectionStyle = 'one',
		                                         sizeStyle = 'small',
		                                         callback = self.btnTextRepresentationCallback)
		self.w.btnTextRepresentation.set(1)


		self.w.textedit = TextEditor((5,28,-5,-30)) #28
		self.w.textedit.getNSTextView().setFont_(NSFont.fontWithName_size_('Menlo', 16))

		self.w.btnCancel = Button((5,-25,120,17),title = 'Cancel',
		                          callback = self.btnCancelCallback, sizeStyle = 'small')
		self.w.btnApply = Button((-125,-25,120,17),title = 'Apply',
		                         callback = self.btnApplyCallback, sizeStyle = 'small')
		self.w.open()

	def btnCancelCallback(self,sender):
		self.w.close()
	def btnApplyCallback(self,sender):
		if self.callback:
			self.callback(self.w.textedit.get())
		self.w.close()


	def convertText(self):
		if self.textMode == 1: # Glyph names
			text = self.w.textedit.get()
			tline = []
			for glyphName in tdGlyphparser.translateText(self.font, text):
				if '00AD' not in glyphName:
					tline.append(glyphName)
			if tline:
				text = '/' + '/'.join(tline)
			self.w.textedit.set(text)
		elif self.textMode == 0: # as Text
			text = self.w.textedit.get()
			tline = ''
			for glyphName in tdGlyphparser.translateText(self.font, text):
				if '00AD' not in glyphName:
					if glyphName in self.font:
						if self.font[glyphName].unicode:
							uni = chr(int("%04X" % (self.font[glyphName].unicode),16))
							tline += uni
						else:
							tline += '/%s ' % glyphName
			if tline:
				self.w.textedit.set(tline)


	def btnTextRepresentationCallback (self, sender):
		self.textMode = sender.get()
		self.convertText()


	def setText(self, text = None):
		if text:
			self.w.textedit.set(text)

# ===================================================================================================
class KernObserver(object):
	def __init__ (self):
		self.w = Window((1080, 600), "KernTool", minSize = (200, 100))
		self.font = CurrentFont()

		rightWall = -5  # -280

		self.w.kernObserver = TDKernObserver((5, 25, rightWall, -234 + 10),
		                           selectionCallback = self.pairSelectionCallback,
		                           refreshCallback = self.refresh,
		                           commandCallback = self.commandsFromObserver,
		                           window = self.w)

		self.w.ctrl3 = TDControlPanel((5, -231 + 10, -5, 17),  # -160
		                                      parentWindow = self,
		                                      selectionCallback = None,
		                                      keyPressedCallback = None)

		self.w.ctrl3.addControlItem(title = 'exception',
		                                    hotkey = 'E',  # callback = self.keyPressedException,
		                                    command = COMMAND_MAKE_EXCEPTION)
		# command = COMMAND_SELECT_FONT,
		# callback = self.w.kernObserver.fontMenuCall)
		self.w.ctrl3.addControlItem(title = 'delete',
		                                    hotkey = chr(int('232B', 16)),
		                                    # callback = self.keyPressedDelete,
		                                    command = COMMAND_DELETE_PAIR)
		self.w.ctrl3.addControlItem(title = '-10',
		                                    hotkey = chr(int('2190', 16)),
		                                    # callback = self.setCurrentPairValue,
		                                    command = COMMAND_SET_KERNING_DEC10,
		                                    callbackValue = -10)
		self.w.ctrl3.addControlItem(title = '-5',
		                                    hotkey = chr(int('21E7', 16)) + chr(int('2190', 16)),
		                                    # callback = self.setCurrentPairValue,
		                                    command = COMMAND_SET_KERNING_DEC5,
		                                    callbackValue = -5)
		self.w.ctrl3.addControlItem(title = '-1',
		                                    hotkey = chr(int('2325', 16)) + chr(int('2190', 16)),
		                                    # callback = self.setCurrentPairValue,
		                                    command = COMMAND_SET_KERNING_DEC1,
		                                    callbackValue = -1)
		self.w.ctrl3.addControlItem(title = '+1',
		                                    hotkey = chr(int('2325', 16)) + chr(int('2192', 16)),
		                                    # callback = self.setCurrentPairValue,
		                                    command = COMMAND_SET_KERNING_INC1,
		                                    callbackValue = 1)
		self.w.ctrl3.addControlItem(title = '+5',
		                                    hotkey = chr(int('21E7', 16)) + chr(int('2192', 16)),
		                                    # callback = self.setCurrentPairValue,
		                                    command = COMMAND_SET_KERNING_INC5,
		                                    callbackValue = 5)
		self.w.ctrl3.addControlItem(title = '+10',
		                                    hotkey = chr(int('2192', 16)),
		                                    # callback = self.setCurrentPairValue,
		                                    command = COMMAND_SET_KERNING_INC10,
		                                    callbackValue = 10)
		self.w.ctrl3.addControlItem(title = chr(int('00D7', 16)),
		                                    hotkey = '0..9')
		self.w.ctrl3.addControlItem(title = 'flip',
		                                    hotkey = 'F',
		                                    # callback = self.setCurrentPairValue,
		                                    command = COMMAND_SET_KERNING_INC10,
		                                    callbackValue = 10)
		self.w.ctrl3.addControlItem(title = 'switch',
		                                    hotkey = chr(int('2325', 16)) + chr(int('F803', 16)),
		                                    # callback = self.setCurrentPairValue,
		                                    command = COMMAND_SET_KERNING_INC10,
		                                    callbackValue = 10)
		self.w.ctrl3.addControlItem(title = 'edit',
		                                    hotkey = chr(int('21B5', 16)),
		                                    # callback = self.setCurrentPairValue,
		                                    command = COMMAND_SET_KERNING_INC10,
		                                    callbackValue = 10)
		self.w.ctrl3.addControlItem(title = 'copy',
		                            hotkey = chr(int('2318', 16)) + 'C',
		                            # callback = self.setCurrentPairValue,
		                            command = COMMAND_SET_KERNING_INC10,
		                            callbackValue = 10)
		self.w.ctrl3.addControlItem(title = 'paste',
		                            hotkey = chr(int('2318', 16)) + 'V',
		                            # callback = self.setCurrentPairValue,
		                            command = COMMAND_SET_KERNING_INC10,
		                            callbackValue = 10)
		# self.w.ctrl3.addControlItem(title = 'SpaceCenter',
		#                                     hotkey = chr(int('F803', 16)) + chr(int('F803', 16)),
		#                                     # callback = self.setCurrentPairValue,
		#                                     command = COMMAND_SET_KERNING_INC10,
		#                                     callbackValue = 10)

		hGRPcontrols = 85

		self.w.groupsView = TDGroupViewLinesAndStackLR(self.w, posSize = (5, -209 + 8, -5, 0),
		                              # selectionCallback = self.lineGroupsSelectionCallback,
		                              selectionPairCallback = self.groupsViewSelectionPairCallback,
		                                               stackedGroupDBLclickCallback = self.stackedGroupViewDblClickCallback
		                              )

		self.w.gcontrol = Group((0, 0, -0, 25))
		self.w.gcontrol.ctrl1 = TDControlPanel((5, 4, -5, 17),
		                                              parentWindow = self,
		                                              selectionCallback = None,
		                                              keyPressedCallback = None)
		self.w.gcontrol.ctrl1.addControlItem(title = 'select font',
		                                            hotkey = 'S',
		                                            command = COMMAND_SELECT_FONT,
		                                            callback = self.fontMenuCall
		                                            )
		self.w.gcontrol.ctrl1.addControlItem(title = 'open file', hotkey = 'O',
		                                            command = COMMAND_OPEN_PAIRS_FILE,
		                                            callback = self.w.kernObserver.openFileCall)
		self.w.gcontrol.ctrl1.addControlItem(title = 'make pairs', hotkey = 'P',
		                                            command = COMMAND_OPEN_PAIRS_BUILDER,
		                                            callback = self.w.kernObserver.pairsBuilderCall)
		self.w.gcontrol.ctrl1.addControlItem(title = 'from selection', hotkey = 'R',
		                                            command = COMMAND_REFRESH,
		                                            callback = self.makePairsFromSelection
		                                            )


		self.w.controlShowTouchedID = self.w.gcontrol.ctrl1.addControlItem(
			title = 'show touches', hotkey = 'T',
			command = COMMAND_SWITCH_TOUCHE_MODE,
			callback = self.w.kernObserver.touchModeSwitch)

		self.w.controlShowValuesID = self.w.gcontrol.ctrl1.addControlItem(
				title = 'show margins', hotkey = 'M',
				command = COMMAND_SWITCH_VALUES_MODE,
				callback = self.w.kernObserver.valuesModeSwitch)

		# self.w.controlCheckTouchedID = self.w.gcontrol.ctrl1.addControlItem(
		# 	title = 'check touches', hotkey = 'C',
		# 	command = COMMAND_CHECK_TOUCHE,
		# 	callback = self.w.kernObserver.findOverlapingGlyphs)

		self.w.controlLightModeID = self.w.gcontrol.ctrl1.addControlItem(
			title = 'light mode', hotkey = 'L',
			command = COMMAND_LIGHT_MODE,
			callback = self.w.kernObserver.lightModeSwitch)

		self.w.controlOffKerningID = self.w.gcontrol.ctrl1.addControlItem(
			title = 'off kerning', hotkey = 'K',
			command = COMMAND_OFF_KERN,
			callback = self.w.kernObserver.offKerning)

		# self.w.gcontrol.ctrl1.addControlItem(title = 'zoom:')
		self.w.gcontrol.ctrl1.addControlItem(title = '', hotkey = '+', visible = False,  # 2295
		                                            command = COMMAND_ZOOM_IN,
		                                            callback = self.w.kernObserver.zoomIn)
		self.w.gcontrol.ctrl1.addControlItem(title = '', hotkey = '-', visible = False,  # 2296
		                                            command = COMMAND_ZOOM_OUT,
		                                            callback = self.w.kernObserver.zoomOut)
		self.w.gcontrol.ctrl1.addControlItem(title = 'next line', visible = False,
		                                            command = COMMAND_NEXT_LINE_SHORT,
		                                            callback = self.w.kernObserver.stepToNextLine)
		self.w.gcontrol.ctrl1.addControlItem(title = 'prev line', visible = False,
		                                            command = COMMAND_PREV_LINE_SHORT,
		                                            callback = self.w.kernObserver.stepToPrevLine)
		self.w.gcontrol.ctrl1.addControlItem(title = 'next block', visible = False,
		                                            command = COMMAND_NEXT_LINE,
		                                            callback = self.w.kernObserver.stepToNextBlock)
		self.w.gcontrol.ctrl1.addControlItem(title = 'prev block', visible = False,
		                                            command = COMMAND_PREV_LINE,
		                                            callback = self.w.kernObserver.stepToPrevBlock)

		self.w.ctrl2 = TDControlPanel((5, -27, -5, 17),
		                                      parentWindow = self,
		                                      selectionCallback = None,
		                                      keyPressedCallback = None)
		self.w.ctrl2.addControlItem(title = 'blocks:')
		self.w.ctrl2.addControlItem(title = '',
		                                    hotkey = chr(int('2325', 16)) + chr(int('2193', 16)),
		                                    command = COMMAND_NEXT_LINE,
		                                    callback = self.w.kernObserver.stepToNextBlock)
		self.w.ctrl2.addControlItem(title = '',
		                                    hotkey = chr(int('2325', 16)) + chr(int('2191', 16)),
		                                    command = COMMAND_PREV_LINE,
		                                    callback = self.w.kernObserver.stepToPrevBlock)

		self.w.ctrl2.addControlItem(title = 'lines:')
		self.w.ctrl2.addControlItem(title = '',
		                                    hotkey = chr(int('2193', 16)),
		                                    command = COMMAND_NEXT_LINE_SHORT,
		                                    callback = self.w.kernObserver.stepToNextLine)
		self.w.ctrl2.addControlItem(title = '',
		                                    hotkey = chr(int('2191', 16)),
		                                    command = COMMAND_PREV_LINE_SHORT,
		                                    callback = self.w.kernObserver.stepToPrevLine)
		self.w.ctrl2.addControlItem(title = 'pairs:')
		self.w.ctrl2.addControlItem(title = '',
		                                    hotkey = chr(int('21E5', 16)))
		self.w.ctrl2.addControlItem(title = '',
		                                    hotkey = chr(int('2325', 16)) + chr(int('21E5', 16)))

		self.w.ctrl2.addControlItem(title = 'show margins', hotkey = 'M', visible = False,
		                                    command = COMMAND_SWITCH_VALUES_MODE,
		                                    callback = self.w.kernObserver.valuesModeSwitch)
		self.w.ctrl2.addControlItem(title = 'show touches', hotkey = 'T', visible = False,
		                                    command = COMMAND_SWITCH_TOUCHE_MODE,
		                                    callback = self.w.kernObserver.touchModeSwitch)
		self.w.ctrl2.addControlItem(title = 'light mode', hotkey = 'L', visible = False,
		                                    command = COMMAND_LIGHT_MODE,
		                                    callback = self.w.kernObserver.lightModeSwitch)
		self.w.ctrl2.addControlItem(title = 'zoom:')
		self.w.ctrl2.addControlItem(title = '', hotkey = '+',
		                                    command = COMMAND_ZOOM_IN,
		                                    callback = self.w.kernObserver.zoomIn)
		self.w.ctrl2.addControlItem(title = '', hotkey = '-',
		                                    command = COMMAND_ZOOM_OUT,
		                                    callback = self.w.kernObserver.zoomOut)

		self.w.ctrl2.addControlItem(title = 'select font', visible = False,
		                                    hotkey = 'F',
		                                    command = COMMAND_SELECT_FONT,
		                                    callback = self.fontMenuCall
		                                    )
		self.w.ctrl2.addControlItem(title = 'open file', hotkey = 'O', visible = False,
		                                    command = COMMAND_OPEN_PAIRS_FILE,
		                                    callback = self.w.kernObserver.openFileCall)
		self.w.ctrl2.addControlItem(title = 'make pairs', hotkey = 'P', visible = False,
		                                    command = COMMAND_OPEN_PAIRS_BUILDER,
		                                    callback = self.w.kernObserver.pairsBuilderCall)
		self.w.ctrl2.addControlItem(title = 'refresh', hotkey = 'R', visible = False,
		                                    command = COMMAND_REFRESH,
		                                    callback = self.makePairsFromSelection
		                                    )
		self.w.ctrl2.addControlItem(title = 'off kerning', hotkey = 'K', visible = False,
		                                    command = COMMAND_OFF_KERN,
		                                    callback = self.w.kernObserver.offKerning
		                                    )

		# sss1 = '2589'
		self.w.ctrl2.addLevelControlItem(title = 'line length',
		                                         min_level = 600,
		                                         max_level = 2600,
		                                         step_level = 200,
		                                         value = 1060,
		                                         callback = self.setCanvasWidth)
		self.w.ctrl2.addMenuSeparator()
		# self.w.ctrl2.addControlItem(title = ' ')
		# self.w.labelTotalGroupsID = self.w.ctrl2.addLabelItem(title = 'groups', value = 0)
		self.w.labelTotalPairsID = self.w.ctrl2.addLabelItem(title = 'pairs', value = 0)
		self.w.ctrl2.addMenuSeparator(type = ' ')
		self.w.labelViewPairsID = self.w.ctrl2.addLabelItem(title = 'shown', value = 0)
		# self.w.ctrl2.addControlItem(title = ' ')
		self.w.ctrl2.addMenuSeparator()
		self.w.labelCurrentPairID = self.w.ctrl2.addLabelItem('', value = 0, separator = '')
		self.w.ctrl2.setLabelValue(self.w.labelTotalPairsID, 0)
		# self.w.ctrl2.setLabelValue(self.w.labelTotalGroupsID, 0)
		# self.w.labelVersion = self.w.ctrl2.addLabelItem(title = 'KernTool', value = 0)
		# self.w.ctrl2.setLabelValue(self.w.labelVersion, KERNTOOL_VERSION)
		self.setCanvasWidth(1000)

		# self.w.gcontrol.ctrl1.selectControlItem(self.w.controlShowTouchedID)

		self.w.bind('close', self.windowCloseCallback)

		addObserver(self.w.kernObserver, 'refreshKernView', EVENT_KERN_VALUE_CHANGED)
		# addObserver(self.w.kernObserver, 'refreshKernViewFromLinked', EVENT_KERN_VALUE_LINKED)
		self.w.bind('resize', self.windowResize)
		# addObserver(self.w.kernObserver, 'stepToLine', EVENT_STEP_TO_LINE)
		# addObserver(self.w.kernObserver, 'sendObserverID', EVENT_OBSERVERID)
		addObserver(self.w.kernObserver, 'setGlyphs', EVENT_OBSERVER_SETTEXT)
		addObserver(self.w.kernObserver, 'refreshKernViewFromOtherObserver', EVENT_REFRESH_ALL_OBSERVERS)

		# addObserver(self, 'refreshFontList', 'fontDidOpen')
		# addObserver(self, 'refreshFontList', 'fontWillClose')

		self.w.open()
		self.hashKernDic = TDHashKernDic(self.font)

		self.w.groupsView.setFont(self.font, self.hashKernDic)
		self.makePairsFromSelection()

	def callbackLevers (self, info):
		pass

	def windowResize(self, sender):
		self.w.gcontrol.ctrl1.updatePanel()
		self.w.ctrl2.updatePanel()
		self.w.ctrl3.updatePanel()
		self.w.groupsView.updatePanel()


	def windowCloseCallback (self, sender):
		removeObserver(self.w.kernObserver, EVENT_KERN_VALUE_CHANGED)
		# removeObserver(self.w.kernObserver, EVENT_KERN_VALUE_LINKED)
		# removeObserver(self.w.kernObserver, EVENT_STEP_TO_LINE)
		# removeObserver(self.w.kernObserver, EVENT_OBSERVERID)
		removeObserver(self.w.kernObserver, EVENT_OBSERVER_SETTEXT)
		removeObserver(self.w.kernObserver, EVENT_REFRESH_ALL_OBSERVERS)
		# print ('KernTool: DONE')

	def setCanvasWidth (self, sender):
		self.visibleWidth = sender
		self.w.kernObserver.recalculateFrame(sender)
		self.w.kernObserver.compileLines()
		self.w.kernObserver.scrollToBlock(self.w.kernObserver._selectedBlock)
		self.w.kernObserver.canvas.update()

	def editLine(self):
		ed = EditLineDialog(parentWindow = self.w, font = self.font, callback = self.getTextFromEditor)
		linesstruct = self.w.kernObserver.getSelectedLineStructured()
		ed.setText(text = linesstruct['text'])

	def getTextFromEditor(self, text):
		# print text
		if text and text != '':
			tline = []
			for glyphName in tdGlyphparser.translateText(self.font, text):
				if glyphName and '00AD' not in glyphName:
					tline.append(glyphName)
			# print tline
			if len(tline) >= 2:
				linesstruct = self.w.kernObserver.getSelectedLineStructured()
				self.w.kernObserver.insertGlyphsToCurrentLinesState(linesstruct['prelines'],
				                                          linesstruct['selectedline'],
				                                          tline,
				                                          linesstruct['postlines'])

	def commandsFromObserver (self, command):
		if command == COMMAND_SELECT_FONT:
			self.fontMenuCall()
		if command == COMMAND_ENTER:
			self.editLine()
		if command == COMMAND_OPEN_LINE_IN_SPACECENTER:
			w = OpenSpaceCenter(self.font)
			w.set(self.w.kernObserver.getSelectedLine())
		if command == COMMAND_OPEN_GLYPH:
			g = self.font[self.w.kernObserver.getSelectedGlyph()]
			if g is not None:
				OpenGlyphWindow(g, newWindow = True)
		# if command == COMMAND_ALT_ENTER:
		# 	print 'COMMAND_ALT_ENTER'

	def stackedGroupViewDblClickCallback(self, info):
		if info and info.startswith(ID_KERNING_GROUP):
			gline = self.font.groups[info]
			w = OpenSpaceCenter(self.font)
			w.set(gline)

	def fontMenuCall (self):
		from mojo.UI import SelectFont
		font = SelectFont(title = 'KernTool')
		self.refresh(font)
		# MenuDialogWindow(parentWindow = self.w, callback = self.refresh)

	def refresh (self, font):
		# print(font)
		if not font:
			self.font = CurrentFont()
		else:
			self.font = font
		self.makePairsFromSelection()


	def makePairsFromSelection (self):
		if self.font and self.font.selection:
			self.hashKernDic = TDHashKernDic(self.font)
			self.w.kernObserver.setFont(self.font, self.hashKernDic)
			self.w.groupsView.setFont(self.font, self.hashKernDic)

			patternLeft = self.font.selection
			patternRight = self.font.selection
			self.w.kernObserver.setLines(left = patternLeft, right = patternRight)
			self.w.setTitle(title = 'KernTool: %s %s' % (self.font.info.familyName, self.font.info.styleName))
		# else:
		# 	print ('Nothing is selected')


	def pairSelectionCallback (self, info):
		if info:
			lp, rp = info
			l = lp['nameUUID']
			r = rp['nameUUID']
			self.w.groupsView.setPair((l, r))

	def groupsViewSelectionPairCallback (self, info):
		self.w.kernObserver.switchPair(info)

	# def lineGroupsSelectionCallback (self, info):
	# 	glyphsline = []
	# 	for glyphname in info:  # sender.get():
	# 		glyphsline.append(glyphname)
	# 	if glyphsline:
	# 		text = '/' + '/'.join(glyphsline)
	# 		postEvent('typedev.KernTool.setGlyphsLine',
	# 		          glyphsLine = text,
	# 		          fontID = getFontID(self.font),
	# 		          observerID = self.w.gC.observerID)
