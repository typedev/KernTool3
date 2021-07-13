# -*- coding: utf-8 -*-

from vanilla import *
from AppKit import *
from fontTools.pens.cocoaPen import CocoaPen
from mojo.canvas import Canvas
from mojo import drawingTools# .drawingTools import *

from fontParts.world import CurrentFont
from lib.eventTools.eventManager import postEvent, publishEvent
from mojo.events import addObserver, removeObserver
from defconAppKit.windows.baseWindow import BaseWindowController
from vanilla.dialogs import getFile, putFile
import codecs, sys, os
import operator

import importlib
import platform

import tdCanvasKeysDecoder
importlib.reload(tdCanvasKeysDecoder)
from tdCanvasKeysDecoder import decodeCanvasKeys, decodeModifiers

import tdKernToolEssentials
importlib.reload(tdKernToolEssentials)
from tdKernToolEssentials import *

import tdControlPanel
importlib.reload(tdControlPanel)
from tdControlPanel import TDControlPanel

import tdGlyphparser
importlib.reload(tdGlyphparser)

import tdMenuAdvanced
importlib.reload(tdMenuAdvanced)
from tdMenuAdvanced import MenuDialogWindow

idY0 = 0
idDispL = 1
idDispR = 2
idKern = 3
idNote = 4
idNameL = 5
idNameR = 6
idGlyphL = 7
idGroupL = 9
idGlyphR = 8
idGroupR = 10

class TDKernDB(object):
	def __init__(self, font, hashKernDic):
		self.font = font
		self.hashKernDic = hashKernDic
		self.db = {}
		self.sortedList = []
		# self.indexList = {}

		self._mask1id = ID_KERNING_GROUP.replace('.kern', '') + ID_GROUP_DIRECTION_POSITION_LEFT
		self._mask2id = ID_KERNING_GROUP.replace('.kern', '') + ID_GROUP_DIRECTION_POSITION_RIGHT

		self.buildDB()



	def buildDB(self):
		self.db = {}
		for pair in self.font.kerning:
			self.refreshPairInDB(pair)

	def makeSortedList(self, pairslist = None, order = 'left', reverse = False):
		if not pairslist:
			pairslist = self.db
		# self.indexList = {}
		if order == 'left':
			self.sortedList = sorted(pairslist.items(), key = lambda p: (p[1][0], p[1][1]), reverse = reverse )
		elif order == 'right':
			self.sortedList = sorted(pairslist.items(), key = lambda p: (p[1][1], p[1][0]), reverse = reverse)
		elif order == 'values':
			self.sortedList = sorted(pairslist.items(), key = lambda p: (p[1][4], p[1][0], p[1][1]), reverse = reverse)
		elif order == 'notes':
			reverse = not reverse
			self.sortedList = sorted(pairslist.items(), key = lambda p: (p[1][5], p[1][0], p[1][1]), reverse = reverse)
		# for idx, item in enumerate(self.sortedList):
		# 	self.indexList[item[0]] = idx

	def refreshPairInDB(self, pair):
		(l,r) = pair
		if pair not in self.font.kerning: return
		v = self.font.kerning[pair]
		keyGlyphL = self.hashKernDic.getKeyGlyphByGroupname(l)  # idGlyphL
		keyGlyphR = self.hashKernDic.getKeyGlyphByGroupname(r)
		note, _l, _r = getKernPairInfo_v2(self.font, self.hashKernDic, (l, r))

		grouppedR = False
		sortR = r
		# print('ref', l,r, _l,_r, note)
		if r.startswith(ID_KERNING_GROUP):
			grouppedR = True
			sortR = r.replace(self._mask2id, '')

		if l.startswith(ID_KERNING_GROUP):
			sortL = l.replace(self._mask1id, '')
			self.db[(l, r)] = (sortL, sortR, True, grouppedR, v, note, keyGlyphL, keyGlyphR)
		else:
			self.db[(l, r)] = (l, sortR, False, grouppedR, v, note, keyGlyphL, keyGlyphR)

		if l != _l and r != _r :
			# print ('i think this pair is Orhan')
			if (_l, _r) in self.db:
				(_sl, _sr, _gl, _gr, _v, note, _kgl, _kgr) = self.db[(_l,_r)]
				self.db[(_l, _r)] = (_sl, _sr, _gl, _gr, _v, PAIR_INFO_ATTENTION, _kgl, _kgr)


	def updateKernPair(self, pair):
		if pair in self.db:
			# print('pair in DB', self.db[pair])
			if pair in self.font.kerning:
				# print ('just new value')
				self.refreshPairInDB(pair)
				# note, _l, _r = getKernPairInfo_v2(self.font, self.hashKernDic, pair)
				# # if note == PAIR_INFO_ORPHAN:
				# print ('but lets check the parents',_l, _r, note)
				# self.refreshPairInDB((_l, _r))

			else:
				# print('but it not in kernig - pair was deleted')
				self.db.pop(pair)

				note, _l, _r = getKernPairInfo_v2(self.font, self.hashKernDic, pair)
				""" теперь, если пара - исключение, надо найти инфу о родительских группах и обновить инфу о них"""
				# if note == PAIR_INFO_ORPHAN or note == PAIR_INFO_EXCEPTION or note == PAIR_INFO_EXCEPTION_DELETED:
				# print('pair was exception, refreshing info about parents', pair, _l, _r)
				if (_l, _r) in self.db:
					# print('founded in db')
					self.refreshPairInDB((_l,_r))
				return pair
		else:
			# print('pair not in DB', pair)
			if pair in self.font.kerning:
				# print ('but it has in kerning, adding new pair in DB')
				self.refreshPairInDB(pair)
				note, _l, _r = getKernPairInfo_v2(self.font, self.hashKernDic, pair)
				""" теперь, если пара - исключение, надо найти инфу о родительских группах и обновить инфу о них"""
				if note == PAIR_INFO_EXCEPTION:# or note == PAIR_INFO_ORPHAN:
					# print('pair new is exception, refreshing info about parents', _l,_r)
					if (_l, _r) in self.db:
						self.refreshPairInDB((_l, _r))
			else:
				print('error! pair not found in DB and kerning', pair)
		return None

	def getKernPair(self, pair):
		if pair in self.db:
			return self.db[pair]
		else:
			print ('DB: pair not founded', pair)



class TDKernListControl(VanillaBaseObject):
	nsViewClass = NSView

	def __init__ (self, posSize, selectionCallback=None, window=None):
		xw, yw, tx, ty = posSize
		# self._window = window
		# self._font = None
		self._viewArray = []
		self._lastSelectedIdx = 0
		self._positionYselected = 0
		self._lineSize = ty  # 1800 # 1800=1000upm; 2400=2000upm
		self._scalefactorUI = 1
		self._lineCount = 1

		self.darkmode = KERNTOOL_UI_DARKMODE
		self.darkmodeWarm = KERNTOOL_UI_DARKMODE_WARMBACKGROUND

		self._xL = 0
		self._xR = 0
		self._xV = 0
		self._xN = 0

		self.maxX = 0

		self._selectionCallback = selectionCallback
		self.showselection = False
		self._setupView(self.nsViewClass, (xw, yw, tx, ty))  # (0, 0, -0, 106)

		self.canvas = Canvas((0, 0, -0, -0),
		                     delegate = self,  # canvasSize = (100, 101),
		                     hasHorizontalScroller = False,
		                     hasVerticalScroller = True,
		                     autohidesScrollers = False,
		                     backgroundColor = NSColor.whiteColor(),
		                     drawsBackground = True,
		                     # acceptsMouseMoved = True
		                     )
		self.canvas.scrollView.getNSScrollView().setBorderType_(NSNoBorder)


	def setupControl(self, leftTitle, rightTitle, kernTitle, noteTitle):

		self.leftTitle = leftTitle['title']
		self.leftName = leftTitle['name']
		self.rightTitle = rightTitle['title']
		self.rightName = rightTitle['name']
		self.kernTitle = kernTitle['title']
		self.kernName = kernTitle['name']
		self.noteTitle = noteTitle['title']
		self.noteName = noteTitle['name']

		self.leftSelected = False
		self.rightSelected = False
		self.kernSelected = False
		self.noteSelected = False

		self.leftReversed = False
		self.rightReversed = False
		self.kernReversed = False
		self.noteReversed = False

	def selectMenuItem(self, menuname, reversed = False):
		if menuname == self.leftName:
			self.leftSelected = True
			self.rightSelected = False
			self.kernSelected = False
			self.noteSelected = False

			self.leftReversed = reversed
			self.rightReversed = False
			self.kernReversed = False
			self.noteReversed = False

		elif menuname == self.rightName:
			self.leftSelected = False
			self.rightSelected = True
			self.kernSelected = False
			self.noteSelected = False

			self.leftReversed = False
			self.rightReversed = reversed
			self.kernReversed = False
			self.noteReversed = False

		elif menuname == self.kernName:
			self.leftSelected = False
			self.rightSelected = False
			self.kernSelected = True
			self.noteSelected = False

			self.leftReversed = False
			self.rightReversed = False
			self.kernReversed = reversed
			self.noteReversed = False

		elif menuname == self.noteName:
			self.leftSelected = False
			self.rightSelected = False
			self.kernSelected = False
			self.noteSelected = True

			self.leftReversed = False
			self.rightReversed = False
			self.kernReversed = False
			self.noteReversed = reversed


	def mouseDown (self, event):
		visibleWidth = self.canvas.scrollView.getNSScrollView().documentVisibleRect().size.width
		visibleHeight = self.canvas.scrollView.getNSScrollView().documentVisibleRect().size.height
		Y_local_pos = self.canvas.scrollView.getNSScrollView().documentVisibleRect().origin.y
		X_window_pos = event.locationInWindow().x
		Y_window_pos = event.locationInWindow().y
		X_local_pos = self.canvas.scrollView.getNSScrollView().documentVisibleRect().origin.x
		Y_local_pos = self.canvas.scrollView.getNSScrollView().documentVisibleRect().origin.y
		xW, yW, x2W, y2W = self.getPosSize()
		x = X_window_pos + X_local_pos  # - self._letterStep
		y = Y_window_pos + y2W + Y_local_pos

		result = None
		if self._xL < x and x < self._xR:
			result = self.leftName
		elif self._xR < x and x < self._xV:
			result = self.rightName

		elif self._xV < x and x < self._xN:
			result = self.kernName
		elif self._xN < x and x < visibleWidth:
			result = self.noteName
		else:
			return

		if result and self._selectionCallback:
			self.selectMenuItem(result, reversed = False)
			self.canvas.update()
			self._selectionCallback(result)

	def updatePanel(self):
		self.canvas.update()


	def recalculateFrame (self, canvaswidth=None):
		# scalefactor = self._scaleUI
		if canvaswidth:
			visibleWidth = canvaswidth
		else:
			visibleWidth = self.canvas.scrollView.getNSScrollView().documentVisibleRect().size.width
		self.visibleWidth = visibleWidth
		visibleHeight = self.canvas.scrollView.getNSScrollView().documentVisibleRect().size.height

		self.canvas._view.setFrame_(NSMakeRect(0, 0, visibleWidth + 20, visibleHeight))
		self.maxX = visibleWidth + 20


	def draw (self):
		# self.recalculateFrame()
		self._viewFontName = 'Menlo'
		self._viewFontSize = 11
		font(self._viewFontName, fontSize = self._viewFontSize)

		self.recalculateFrame()

		visibleWidth = self.canvas.scrollView.getNSScrollView().documentVisibleRect().size.width
		visibleHeight = self.canvas.scrollView.getNSScrollView().documentVisibleRect().size.height

		Y_local_pos = self.canvas.scrollView.getNSScrollView().documentVisibleRect().origin.y
		X_local_pos = self.canvas.scrollView.getNSScrollView().documentVisibleRect().origin.x

		Y_min_window = Y_local_pos
		Y_max_window = Y_local_pos + visibleHeight

		X_min_window = X_local_pos
		X_max_window = X_local_pos + visibleWidth

		stroke(0, 0, 0, 0)
		strokeWidth(0)

		colorBKG = (.9, .9, .9, .8)
		if self.darkmode:
			colorBKG = (.1,.1,.1,1)

		fillRGB(colorBKG)
		rect(0, 0, visibleWidth, Y_max_window)

		save()

		Xpos = 0
		Ypos = 0 #item['y0']
		Ycontrol = -1 * Ypos

		wValue = 40  # width of Value row
		wNote = 40  # width of Note row
		w = visibleWidth - wValue - wNote
		xR = w / 2  # width of Left/Right row and start position of Right row
		xV = xR + (w / 2)  # start position Values row
		xN = xV + wValue  # start position Note row

		self._xR = xR
		self._xV = xV
		self._xN = xN

		colorBKG = (.7, .7, .7, .8)
		colorTXT = COLOR_BLACK
		selected = False
		colorGRP = COLOR_GREY_50


		colorBKG = (.9, .9, .9, .8)
		colorSRT = (.85, .85, .85, .8)
		colorTXT = COLOR_BLACK
		selected = False
		colorGRP = COLOR_GREY_30
		colorStroke = COLOR_GREY_50
		if self.darkmode:
			colorBKG = (.2, .2, .2, 1)
			colorSRT = (.85, .85, .85, .8)
			colorTXT = (1,.6,.2,1)
			selected = False
			colorGRP = (.1, .1, .1, 1)
			colorStroke = COLOR_BLACK


		fillRGB(colorStroke)
		rect(0, 0, visibleWidth, Y_max_window)

		txtup = 2.5
		titleY = -2
		txtsm = txtup + 1
		ltxt = self.leftTitle
		rtxt = self.rightTitle

		if self.leftSelected:
			fillRGB(colorGRP)
			rect(Xpos, Ycontrol+1, xR-1, self._lineSize)

			font(self._viewFontName, fontSize = self._viewFontSize)
			fillRGB(colorTXT)
			if self.leftReversed:
				text(chr(int('25B2', 16)), (xR - 17, Ycontrol + txtup))
			else:
				text(chr(int('25BC',16)), (xR - 17, Ycontrol + txtup))
			if not ltxt:
				font(self._viewFontName, fontSize = self._viewFontSize+3)
				text(chr(int('25E7', 16)), (Xpos + 5, Ycontrol + txtup + titleY))
		else:
			fillRGB(colorBKG)
			rect(Xpos, Ycontrol+1, xR-1, self._lineSize)

			font(self._viewFontName, fontSize = self._viewFontSize)
			fillRGB(COLOR_GREY_50)
			if self.leftReversed:
				text(chr(int('25B2', 16)), (xR - 17, Ycontrol + txtup))
			else:
				text(chr(int('25BC', 16)), (xR - 17, Ycontrol + txtup))
			if not ltxt:
				font(self._viewFontName, fontSize = self._viewFontSize+3)
				text(chr(int('25E7', 16)), (Xpos + 5, Ycontrol + txtup + titleY))

		fillRGB(colorTXT)

		if ltxt:
			_w, _h = textSize(ltxt)
			if _w + 5 + 17 > xR:
				font(self._viewFontName, fontSize = self._viewFontSize - 2)
				text(ltxt, (Xpos + 5, Ycontrol + txtsm + titleY))
			else:
				font(self._viewFontName, fontSize = self._viewFontSize )
				text(ltxt, (Xpos + 5, Ycontrol + txtsm + titleY))


		# DRAW Right row
		if self.rightSelected:
			fillRGB(colorGRP)
			rect(xR, Ycontrol+1, xR-1, self._lineSize)

			font(self._viewFontName, fontSize = self._viewFontSize)
			fillRGB(colorTXT)
			if self.rightReversed:
				text(chr(int('25B2', 16)), (xV - 17, Ycontrol + txtup))
			else:
				text(chr(int('25BC', 16)), (xV - 17, Ycontrol + txtup))
			if not rtxt:
				font(self._viewFontName, fontSize = self._viewFontSize + 3)
				text(chr(int('25E8', 16)), (xR + 5, Ycontrol + txtup + titleY))
		else:
			fillRGB(colorBKG)
			rect(xR, Ycontrol+1, xR-1, self._lineSize)

			font(self._viewFontName, fontSize = self._viewFontSize)
			fillRGB(COLOR_GREY_50)
			if self.rightReversed:
				text(chr(int('25B2', 16)), (xV - 17, Ycontrol + txtup))
			else:
				text(chr(int('25BC', 16)), (xV - 17, Ycontrol + txtup))
			if not rtxt:
				font(self._viewFontName, fontSize = self._viewFontSize + 3)
				text(chr(int('25E8', 16)), (xR + 5, Ycontrol + txtup + titleY))

		fillRGB(colorTXT)

		if rtxt:
			_w, _h = textSize(rtxt)
			if _w + 17 > xR:
				font(self._viewFontName, fontSize = self._viewFontSize - 2)
				text(rtxt, (xR + 5, Ycontrol + txtsm + titleY))
			else:
				font(self._viewFontName, fontSize = self._viewFontSize)
				text(rtxt, (xR + 5, Ycontrol + txtup + titleY))

		if self.kernSelected:
			fillRGB(colorGRP)
			rect(xV, Ycontrol+1, wValue-1, self._lineSize)
			font(self._viewFontName, fontSize = self._viewFontSize)
			fillRGB(colorTXT)

			if self.kernReversed:
				text(chr(int('25B2', 16)), (xN - 17, Ycontrol + txtup))
			else:
				text(chr(int('25BC', 16)), (xN - 17, Ycontrol + txtup))
		else:
			fillRGB(colorBKG)
			rect(xV, Ycontrol+1, wValue-1, self._lineSize)

			font(self._viewFontName, fontSize = self._viewFontSize)
			fillRGB(COLOR_GREY_50)

			if self.kernReversed:
				text(chr(int('25B2', 16)), (xN - 17, Ycontrol + txtup))
			else:
				text(chr(int('25BC', 16)), (xN - 17, Ycontrol + txtup))

		fillRGB(colorTXT)
		rtxt = self.kernTitle
		_w, _h = textSize(rtxt)
		if _w + 17 > wValue:
			font(self._viewFontName, fontSize = self._viewFontSize - 2)
			text(rtxt, (xV + 5, Ycontrol + txtsm+ titleY))
		else:
			font(self._viewFontName, fontSize = self._viewFontSize)
			text(rtxt, (xV + 5, Ycontrol + txtup+ titleY))

		if self.noteSelected:
			fillRGB(colorGRP)
			rect(xN, Ycontrol+1, wNote, self._lineSize)
			fillRGB(colorTXT)
			font(self._viewFontName, fontSize = self._viewFontSize)
			if self.noteReversed:
				text(chr(int('25B2', 16)), (xN + 8, Ycontrol + txtup))
			else:
				text(chr(int('25BC', 16)), (xN + 8, Ycontrol + txtup))
		else:
			fillRGB(colorBKG)
			rect(xN, Ycontrol+1, wNote, self._lineSize)
			fillRGB(COLOR_GREY_50)
			font(self._viewFontName, fontSize = self._viewFontSize)
			if self.noteReversed:
				text(chr(int('25B2', 16)), (xN + 8, Ycontrol + txtup))
			else:
				text(chr(int('25BC', 16)), (xN + 8, Ycontrol + txtup))

		fillRGB(colorTXT)
		rtxt = self.noteTitle
		_w, _h = textSize(rtxt)
		if _w + 17 > wNote:
			font(self._viewFontName, fontSize = self._viewFontSize - 2)
			text(rtxt, (xN + 5, Ycontrol + txtsm+ titleY))
		else:
			font(self._viewFontName, fontSize = self._viewFontSize)
			text(rtxt, (xN + 5, Ycontrol + txtup+ titleY))
		restore()


idModeSelected = False
idModeShowAll = True
idFilterSide1 = 'side1'
idFilterBoth = 'both'
idFilterSide2 = 'side2'

class TDKernListView(VanillaBaseObject):
	nsViewClass = NSView
	def __init__ (self, posSize, selectionCallback=None, window=None, commandCallback = None, previewGlyph = False):
		xw, yw, tx, ty = posSize
		self._window = window
		self._linesToDisplay = []
		# self._font = None
		self.font = None
		self.hashKernDic = None
		self.kernDB = None

		self._viewArray = []
		self._selectedLines = []
		self._pairsList2idx = {}

		self._currentKernListState = {}
		self._setToView = []
		self._grouppedList = []
		self._idxListGroupped = {}
		self._ungrouppedList = []
		self._idxListUngroupped = {}
		self._listKeyGlyphsLeft = {}
		self._listKeyGlyphsRight = {}
		self._errorpairslist = []

		self._lastSelectedIdx = 0
		self._positionYselected = 0

		self._lineSize = 20  # 1800 # 1800=1000upm; 2400=2000upm
		self._previewGlyph = previewGlyph
		self._previewWidthHalf = 40
		if previewGlyph:
			self._lineSize = 45

		self._scalefactorUI = 1
		self._lineCount = 0
		self._sortName = None
		self._sortReverse = None

		self.groupsSortedTop = False

		self._viewingMode = idModeSelected
		self._filterMode = idFilterBoth
		self.darkmode = KERNTOOL_UI_DARKMODE
		self.darkmodeWarm = KERNTOOL_UI_DARKMODE_WARMBACKGROUND

		self.maxX = 0

		self._selectionCallback = selectionCallback
		self._commandCallback = commandCallback
		self.showselection = False
		self._setupView(self.nsViewClass, (xw, yw, tx, ty))  # (0, 0, -0, 106)

		self.macos = MACOS_VERSION

		self.canvas = Canvas((0, 0, -0, -0),
		                     delegate = self,  # canvasSize = (100, 101),
		                     hasHorizontalScroller = False,
		                     hasVerticalScroller = True,
		                     autohidesScrollers = True,
		                     # backgroundColor = NSColor.whiteColor(),
		                     drawsBackground = False,
		                     # acceptsMouseMoved = True
		                     )
		self.canvas.scrollView.getNSScrollView().setBorderType_(NSNoBorder)

	def updatePanel(self):
		self.canvas.update()


	def getCorrectPreviwWidth(self):
		# g = list('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
		# list(filter(lambda n: n.name in g, self.font))
		s = sorted(self.font, key = lambda w: w.width)
		wp = s[-1].width * .030
		self._previewWidthHalf = wp + 10
		if self._previewWidthHalf > 75:
			self._previewWidthHalf = 75

	def setFont(self, font):
		self.font = font
		self.hashKernDic = TDHashKernDic(font)
		self.kernDB = TDKernDB(self.font, self.hashKernDic)
		# self.kernDB.makeSortedList()
		self.getCorrectPreviwWidth()
		self.refreshView()

	def updateStatusbar(self):
		self._window.menuStatusBar.setLabelValue(self._window.labelTotalPairsID, str(len(self.font.kerning)))
		self._window.menuStatusBar.setLabelValue(self._window.labelShowedPairsID, str(len(self._viewArray)))
		self._window.menuStatusBar.setLabelValue(self._window.labelSelectedPairsID, str(len(self._selectedLines)))


	def setPreviewMode(self, previewMode = False):
		self._previewGlyph = previewMode
		self._lineSize = 20  # 1800 # 1800=1000upm; 2400=2000upm
		if self._previewGlyph:
			self._lineSize = 45
		self.refreshView()
		self.scrollToLine(0)


	def resetView(self):
		self.compileLines(self.kernDB.db, sorting = self._sortName, reverse = self._sortReverse)
		self.scrollToLine(0)


	def setViewingMode(self, mode = idModeShowAll, sorting = None, reverse = False, filterMode = idFilterBoth):
		self._viewingMode = mode
		self._filterMode = filterMode
		if sorting:
			self._sortName = sorting
		if reverse:
			self._sortReverse = reverse
		else:
			if reverse != self._sortReverse:
				self._sortReverse = reverse
		if self._viewingMode == idModeSelected:
			self.setGlyphsToView(self.font.selection, filterMode = filterMode)
		else:
			self.compileLines(self.kernDB.db, sorting = self._sortName, reverse = self._sortReverse)
		self.scrollToLine(0)

	def refreshView(self, fullrefresh = True):
		if self._viewingMode == idModeSelected:
			self.setGlyphsToView(self.font.selection, filterMode = self._filterMode)
		else:
			if fullrefresh:
				self.compileLines(self.kernDB.db, sorting = self._sortName, reverse = self._sortReverse)


	def scrollToLine (self, linenumber):
		if not self._viewArray: return
		visibleWidth = self.canvas.scrollView.getNSScrollView().documentVisibleRect().size.width
		visibleHeight = self.canvas.scrollView.getNSScrollView().documentVisibleRect().size.height
		posXscroller = self.canvas.scrollView.getNSScrollView().documentVisibleRect().origin.x
		posYscroller = self.canvas.scrollView.getNSScrollView().documentVisibleRect().origin.y
		scale = self._scalefactorUI
		xpos = 0
		ypos = 0
		if linenumber < 0 or linenumber > len(self._viewArray): return
		self._selectedLine = linenumber
		self._positionYselected = self._viewArray[linenumber][idY0]
		firstItemInLine = linenumber

		maxY = self._viewArray[-1][idY0]
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


	def mouseDown (self, event):
		visibleHeight = self.canvas.scrollView.getNSScrollView().documentVisibleRect().size.height
		Y_local_pos = self.canvas.scrollView.getNSScrollView().documentVisibleRect().origin.y
		X_window_pos = event.locationInWindow().x
		Y_window_pos = event.locationInWindow().y
		X_local_pos = self.canvas.scrollView.getNSScrollView().documentVisibleRect().origin.x
		Y_local_pos = self.canvas.scrollView.getNSScrollView().documentVisibleRect().origin.y
		xW, yW, x2W, y2W = self.getPosSize()
		x = X_window_pos + X_local_pos  # - self._letterStep
		y = Y_window_pos + y2W + Y_local_pos

		self.showselection = True
		maxY = 0
		if self._viewArray:
			maxY = self._viewArray[-1][idY0]
		yoff = ((self._lineCount - 1) * self._lineSize)  # + Ygap
		if yoff < visibleHeight:
			yoff = visibleHeight - self._lineSize * self._lineCount
		else:
			yoff = 0
		for idx, item in enumerate(self._viewArray):
			y0 = maxY + (-1 * item[idY0]) + yoff
			y1 = y0 + self._lineSize
			if (y0 < y and y < y1):
				if decodeModifiers(event.modifierFlags()) == 'Cmd':
					if idx in self._selectedLines:
						self._selectedLines.remove( idx )
					else:
						self._selectedLines.append( idx )
					self._lastSelectedIdx = idx
				elif decodeModifiers(event.modifierFlags()) == 'Shift':
					if idx > self._lastSelectedIdx:
						for i in range(self._lastSelectedIdx, idx+1):
							if i not in self._selectedLines:
								self._selectedLines.append( i )
								self._lastSelectedIdx = i
					elif idx < self._lastSelectedIdx:
						# print ('revers')
						for i in range(idx, self._lastSelectedIdx):
							if i not in self._selectedLines:
								self._selectedLines.append( i )
								self._lastSelectedIdx = i
					# print ('shift last', self._lastSelectedIdx)
				else:
					self._selectedLines = []
					self._selectedLines.append( idx )
					self._lastSelectedIdx = idx

				self.canvas.update()
				self.updateStatusbar()
				if self._selectionCallback:
					self._selectionCallback(self._selectedLines)
				break

	def keyDown (self, event):
		keypress = decodeCanvasKeys(event.keyCode(), event.modifierFlags())
		commands = translateKeyCodesToKernToolCommands(keypress)

		# if commands['command'] == COMMAND_ENTER:
		# 	self.showselection = True
		# 	self.menuSelectedCallback()
		# 	self.canvas.update()
		if commands['command'] == COMMAND_ESCAPE:
			self._selectedLines = []
			self.canvas.update()

		if commands['command'] == COMMAND_SELECT_ALL:
			self._selectedLines = []
			for i, item in enumerate(self._viewArray):
				self._selectedLines.append(i)
			self.updateStatusbar()
			self.canvas.update()


		if commands['command'] == COMMAND_DELETE_PAIR:
			# self.showselection = True
			if self._commandCallback:
				self._commandCallback({'command': COMMAND_DELETE_PAIR})


		if commands['command'] == COMMAND_SPACEKEY:
			self.prepare4sendSelectedPairsToKernTool()

		if commands['command'] == COMMAND_NEXT_LINE_SHORT:
			n = self._lastSelectedIdx + 1
			if n > len(self._viewArray)-1:
				n = 0
			self.scrollToLine(n)
			item = self._viewArray[n]
			# if decodeModifiers(event.modifierFlags()) == 'Shift':
			# 	if item['idx'] in self._selectedLines:
			# 		self._selectedLines.remove(item['idx'])
			# 	else:
			# 		self._selectedLines.append(item['idx'])
			# 	self._lastSelectedIdx = item['idx']
			# else:
			self._selectedLines = []
			self._selectedLines.append(n)
			self._lastSelectedIdx = n


			self.canvas.update()
		if commands['command'] == COMMAND_PREV_LINE_SHORT:
			n = self._lastSelectedIdx - 1
			if n == -1:
				n = len(self._viewArray)-1
			self.scrollToLine(n)
			item = self._viewArray[n]
			# if decodeModifiers(event.modifierFlags()) == 'Shift':
			# 	if item['idx'] in self._selectedLines:
			# 		self._selectedLines.remove(item['idx'])
			# 	else:
			# 		self._selectedLines.append(item['idx'])
			# 	self._lastSelectedIdx = item['idx']
			# else:
			self._selectedLines = []
			self._selectedLines.append(n)
			self._lastSelectedIdx = n

			self.canvas.update()
			self.updateStatusbar()

	def refreshKernPair(self, pair):
		self.kernDB.updateKernPair(pair)

		# save selected pairs
		pairsselected = []
		for i in self._selectedLines:
			item = self._viewArray[i]
			pairsselected.append((item[idNameL], item[idNameR]))
		self._selectedLines = []
		self.refreshView()

		# restore selected pairs, except deleted
		for pair in pairsselected:
			if pair in self._pairsList2idx:
				self._selectedLines.append(self._pairsList2idx[pair])

		self.canvas.update()


	def setGlyphsToView(self, glyphlist, filterMode = idFilterBoth):
		self._currentKernListState = {}
		listL = []
		listR = []
		if not glyphlist: return
		self._setToView = []
		# self._setToView = list(glyphlist)
		for glyphname in glyphlist:
			if filterMode == idFilterSide1 or filterMode == idFilterBoth:
				self._setToView.append(glyphname)
				self._setToView.append(self.hashKernDic.getGroupNameByGlyph(glyphname, side = 'L'))
			if filterMode == idFilterSide2 or filterMode == idFilterBoth:
				self._setToView.append(glyphname)
				self._setToView.append(self.hashKernDic.getGroupNameByGlyph(glyphname, side = 'R'))

		for pair, item in self.kernDB.db.items():
			(l,r) = pair
			# if l in self._setToView or r in self._setToView:
			if l in self._setToView and (filterMode == idFilterSide1 or filterMode == idFilterBoth):
				self._currentKernListState[(l, r)] = item
			if r in self._setToView and (filterMode == idFilterSide2 or filterMode == idFilterBoth):
				self._currentKernListState[(l, r)] = item
		if self._currentKernListState:
			self.compileLines(self._currentKernListState, sorting = self._sortName, reverse = self._sortReverse)
		else:
			self._viewArray = []
			# self.resetView()
		self.canvas.update()
		self.updateStatusbar()


	def getPairByIndex(self, idx):
		try:
			item = self._viewArray[idx]
		except:
			print ('wrong index of pair',idx)
			return None
		l, r, n, kl, kr = item[idNameL], item[idNameR], item[idNote], self.hashKernDic.getKeyGlyphByGroupname(item[idNameL]), self.hashKernDic.getKeyGlyphByGroupname(item[idNameR])
		if n == PAIR_INFO_EMPTY:
			return None
		if (l,r) in self.font.kerning:
			return (l,r, kl,kr)
		else:
			print('pair not founded', l,r)


	def getListofSelectedPairs_KeyGlyphs(self):
		pairs = []
		leftlist = []
		rightlist = []
		pairsbyglyphkey = []
		if self._selectedLines:
			for idx in sorted(self._selectedLines):
				p = self.getPairByIndex(idx)
				if p:
					pairs.append(self.getPairByIndex(idx))
				# print(self.getPairByIndex(idx))
			for pair in pairs:
				l,r, kl, kr = pair
				if l.startswith(ID_KERNING_GROUP):
					if l in self.font.groups and len(self.font.groups[l])>0:
						l = self.font.groups[l][0]
				# else:
				# 	leftlist.append(l)
				if r.startswith(ID_KERNING_GROUP):
					if r in self.font.groups and len(self.font.groups[r])>0:
						r = self.font.groups[r][0]
				# else:
				# 	rightlist.append(r)
				if l and r:
					pairsbyglyphkey.append((l,r))
		return pairsbyglyphkey


	def getListOfSelectedPairs(self):
		pairs = []
		if self._selectedLines:
			for idx in sorted(self._selectedLines):
				p = self.getPairByIndex(idx)
				if p:
					l, r, kl, kr = self.getPairByIndex(idx)
					pairs.append((l,r))
		return pairs


	def prepare4sendSelectedPairsToKernTool(self):
		if self._commandCallback:
			pairs = self.getListofSelectedPairs_KeyGlyphs()
			# print (pairs)
			self._commandCallback({'command':COMMAND_SPACEKEY, 'pairs': pairs})


	def compileLines(self, listkern = None, sorting = 'left', reverse = False):

		lineStep = self._lineSize
		# if not listkern: return
		self._viewArray = []
		self._pairsList2idx = {}

		self._sortName = sorting
		self._sortReverse = reverse

		Ypos = 0
		idx = 0
		self._currentKernListState = listkern
		self.kernDB.makeSortedList(self._currentKernListState, order = sorting, reverse = reverse)
		# print(self.kernDB.sortedList)
		for item in self.kernDB.sortedList:
			l , r = item[0]
			sl, sr, gl, gr, v, n, kgl, kgr = item[1]
			self._viewArray.append([
								Ypos,                       # idY0
								sl, #getDisplayNameGroup(l),     # idDispL
								sr, #getDisplayNameGroup(r),     # idDispR
								v,                          # idKern
								n,                          # idNote
								l,                          # idNameL
								r,                          # idNameR
								kgl, #self.hashKernDic.getKeyGlyphByGroupname(l),                         # idGlyphL
								kgr, #self.hashKernDic.getKeyGlyphByGroupname(r),                         # idGlyphR
								gl,                         # idGroupL
								gr                          # idGroupR
							])
			self._pairsList2idx[(l, r)] = idx
			Ypos += lineStep
			idx += 1
			self._lineCount = idx

		self.recalculateFrame()
		self.canvas.update()
		self.updateStatusbar()

	def recalculateFrame (self, canvaswidth=None):
		# scalefactor = 1#self._scalefactorUI
		if canvaswidth:
			visibleWidth = canvaswidth
		else:
			visibleWidth = self.canvas.scrollView.getNSScrollView().documentVisibleRect().size.width
		self.visibleWidth = visibleWidth
		visibleHeight = self.canvas.scrollView.getNSScrollView().documentVisibleRect().size.height

		Y_local_pos = self.canvas.scrollView.getNSScrollView().documentVisibleRect().origin.y
		X_local_pos = self.canvas.scrollView.getNSScrollView().documentVisibleRect().origin.x

		yoff = self._lineCount * self._lineSize #* scalefactor  # + self.Ygap*2
		Y_min_window = Y_local_pos
		Y_max_window = Y_local_pos + visibleHeight

		if yoff < visibleHeight:
			yoff = visibleHeight
		self.canvas._view.setFrame_(NSMakeRect(0, 0, visibleWidth, yoff))
		self.maxX = visibleWidth + 60

	def scrollwheel (self, event):
		# print (event)
		#
		scaleUI = self._scalefactorUI
		# deltaX = event.deltaX()
		deltaY = event.deltaY()
		if deltaY == 0 : return

		scaleScroll = 5#abs(deltaY)/10
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
		# xpoint = posXscroller - (deltaX * scaleScroll)
		ypoint = posYscroller + (deltaY * scaleScroll)
		# if xpoint > self.maxXX - visibleWidth:  # - visibleWidth:
		# 	xpoint = self.maxXX - visibleWidth  # - self.visibleWidth #- visibleWidth
		# if xpoint < xW:
		# 	xpoint = 0

		if ypoint < 0:
			ypoint = 0
		# return
		maxY = 0
		if self._viewArray:
			maxY = (self._lineCount -1) * self._lineSize # self._viewArray[-1]['y0']

		if posYscroller + visibleHeight - self._lineSize * scaleUI > maxY * scaleUI:
			ypoint = maxY * scaleUI - visibleHeight + self._lineSize * scaleUI
		elif posYscroller + visibleHeight - self._lineSize * scaleUI == maxY * scaleUI and deltaY > 0:
			ypoint = maxY * scaleUI - visibleHeight + self._lineSize * scaleUI

		point = NSPoint(0, ypoint)
		self.canvas.scrollView.getNSScrollView().contentView().scrollToPoint_(point)
		self.canvas.scrollView.getNSScrollView().reflectScrolledClipView_(
			self.canvas.scrollView.getNSScrollView().contentView())
		# time.sleep(0.09)
		if self.macos == '15':
			self.canvas.update()
		if self.macos == '16':
			self.canvas.update()
		# self.canvas.update()

	def draw (self):
		def drawException (x, y):
			s = 1.6
			newPath()
			moveTo((x + s * 4, y + s * 8))
			lineTo((x + s * 1, y + s * 3))
			lineTo((x + s * 4, y + s * 3))
			lineTo((x + s * 4, y + s * 0))
			lineTo((x + s * 7, y + s * 5))
			lineTo((x + s * 4, y + s * 5))
			closePath()
			drawPath()

		self.recalculateFrame()
		self._viewFontName = 'Menlo'
		self._viewFontSize = 12
		font(self._viewFontName, fontSize = self._viewFontSize)

		visibleWidth = self.canvas.scrollView.getNSScrollView().documentVisibleRect().size.width
		visibleHeight = self.canvas.scrollView.getNSScrollView().documentVisibleRect().size.height

		Y_local_pos = self.canvas.scrollView.getNSScrollView().documentVisibleRect().origin.y
		X_local_pos = self.canvas.scrollView.getNSScrollView().documentVisibleRect().origin.x

		Y_min_window = Y_local_pos
		Y_max_window = Y_local_pos + visibleHeight
		# print (Y_min_window, Y_max_window, visibleHeight)
		X_min_window = X_local_pos
		X_max_window = X_local_pos + visibleWidth

		stroke(0, 0, 0, 0)
		strokeWidth(0)
		yoff = ((self._lineCount - 1) * self._lineSize) #+ Ygap

		if yoff < visibleHeight:
			yoff = visibleHeight - self._lineSize  #+ 500

		# if self._viewArray:
		# 	maxY = self._viewArray[-1]['y0']
		maxY = (self._lineCount -1) * self._lineSize

		colorBKG = (.9, .9, .9, .8)
		# self.darkmode = True
		if self.darkmode:
			colorBKG = ((.07,.07,.07,1))
		fillRGB(colorBKG)
		rect(0, 0, visibleWidth, Y_max_window)

		save()
		translate(0, yoff )
		Xpos = 0
		Ypos = 0
		XtextShift = 17
		for idx, item in enumerate(self._viewArray):
			# Xpos = item['x0']
			# Ypos = item['y0']
			item[idY0] = Ypos
			# (_d0, _d1,_d2,_d3,_d4,_d5)
			# DRAW if it visible in window frame
			if (Y_min_window - self._lineSize < ((maxY + (-1 * Ypos)))
			    and Y_max_window + self._lineSize > ((maxY + (-1 * Ypos)))) :

				Ycontrol = -1 * Ypos

				wValue = 40 # width of Value row
				wNote = 40  # width of Note row
				w = visibleWidth-wValue-wNote # width of left+right row
				xR = w / 2 # width of Left/Right row and start position of Right row
				xRp = xR
				wtxt = xR
				xV = xR + (w / 2) # start position Values row
				xN = xV + wValue  # start position Note row
				textYshif = 0
				phalf = 0
				if self._previewGlyph:
					phalf = self._previewWidthHalf
					xR += phalf
					wtxt -= phalf
					textYshif = self._lineSize /2 -10


				colorBKG = (.9, .9, .9, .8)
				colorSRT = (.85,.85,.85,.8)
				colorTXT = COLOR_BLACK
				selected = False
				colorGRP = COLOR_GREY_50
				# self.darkmode = True
				if self.darkmode:
					colorBKG = ((.18,.18,.18,.8))
					colorSRT = ((.12,.12,.12,.8))
					colorTXT = (COLOR_GREY_20)
					colorGRP = (COLOR_GREY_50)

				if idx in self._selectedLines:

					colorBKG = (0,0,.5,.6)
					if self.darkmode:
						colorBKG = (.18,.18,.9,.6)
					colorTXT = COLOR_WHITE
					selected = True
					colorGRP = COLOR_GREY_10
					fillRGB(colorBKG)
					if not self._previewGlyph:
						rect(Xpos, Ycontrol, visibleWidth, self._lineSize)
					else:
						rect(Xpos, Ycontrol, xRp - phalf, self._lineSize)
						rect(xR, Ycontrol, wtxt + wValue + wNote, self._lineSize)
						# rect(xV, Ycontrol, wValue, self._lineSize)


				if item[idKern] < 0:
					colorKRN = COLOR_KERN_VALUE_NEGATIVE
					if selected:
						colorKRN = (1,.2,.2,1)
				elif item[idKern] > 0:
					colorKRN = COLOR_KERN_VALUE_POSITIVE
					if selected:
						colorKRN = (0.4,1,0.4,1)
				else:
					colorKRN = colorTXT
				
				# DRAW Left row
				if self._sortName == 'left' and not selected:
					fillRGB(colorSRT)
					# if self._previewGlyph:
					# 	fillRGB(COLOR_GREY_30)
				else:
					fillRGB(colorBKG)

				rect(Xpos, Ycontrol, xRp-phalf, self._lineSize)
				if item[idGroupL]:#.startswith('@.'):
					fillRGB(colorGRP)
					text('@', (Xpos + 5, Ycontrol + 4 + textYshif))


				if self._previewGlyph:

					if selected:
						fillRGB((.3, .3, .3, .5))
						rect(xRp - phalf, Ycontrol, phalf * 2, self._lineSize)
					# else:
					# 	fillRGB((.9, .9, .9, .8))
					# 	rect(xRp - phalf, Ycontrol , phalf * 2, self._lineSize )

				fillRGB(colorTXT)
				ltxt = item[idDispL]
				_w,_h = textSize(ltxt)
				if _w + 5 + XtextShift > wtxt :
					font(self._viewFontName, fontSize = self._viewFontSize-2)
					text( ltxt, (Xpos + XtextShift, Ycontrol+4+ textYshif))
				else:
					font(self._viewFontName, fontSize = self._viewFontSize )
					text( ltxt, (Xpos + XtextShift, Ycontrol + 3+ textYshif))

				if self._previewGlyph:

					if selected:
						fillRGB((.9, .9, .9, .8))
						rect(xRp - phalf, Ycontrol, phalf * 2, self._lineSize)
					else:
						fillRGB((.9, .9, .9, .8))
						if self.darkmode:
							fillRGB((.8, .8, .8, .8))
						rect(xRp - phalf, Ycontrol , phalf * 2, self._lineSize )

				# DRAW Right row
				if self._sortName == 'right' and not selected:
					fillRGB(colorSRT)
					# if self._previewGlyph:
					# 	fillRGB(COLOR_GREY_30)
				else:
					fillRGB(colorBKG)

				rect(xR, Ycontrol, wtxt, self._lineSize)
				font(self._viewFontName, fontSize = self._viewFontSize)
				if item[idGroupR]:#.startswith('@.'):
					fillRGB(colorGRP)
					text('@', (xR + 5, Ycontrol + 4+ textYshif))

				fillRGB(colorTXT)
				rtxt = item[idDispR]
				_w, _h = textSize(rtxt)
				if _w + XtextShift +5 >  wtxt :
					font(self._viewFontName, fontSize = self._viewFontSize - 2)
					text(rtxt, (xR + XtextShift, Ycontrol + 4+ textYshif))
				else:
					font(self._viewFontName, fontSize = self._viewFontSize)
					text(rtxt, (xR + XtextShift, Ycontrol + 3+ textYshif))



				if self._sortName == 'values' and not selected:
					fillRGB(colorSRT)
					# if self._previewGlyph:
					# 	fillRGB(COLOR_GREY_30)
				else:
					fillRGB(colorBKG)
				font('Menlo', fontSize = self._viewFontSize-1)
				# if selected:
				# 	fillRGB((.3,.3,.3,.3))
				rect(xV, Ycontrol, wValue, self._lineSize)
				# openTypeFeatures(tnum = True)
				alignX, _y = textSize(str(item[idKern]))
				alignX = xV + wValue - alignX

				fillRGB(colorKRN)

				# roundedRect(x, y, width, height, radius)

				text(str(item[idKern]), (alignX - 5, Ycontrol + 3))
				font(self._viewFontName, fontSize = self._viewFontSize)

				if self._sortName == 'notes' and not selected:
					fillRGB(colorSRT)
					# if self._previewGlyph:
					# 	fillRGB(COLOR_GREY_30)
				else:
					fillRGB(colorBKG)
				rect(xN, Ycontrol, wNote, self._lineSize)
				fillRGB(colorTXT)

				if PAIR_INFO_EXCEPTION == item[idNote]:
					fillRGB(colorKRN)
					drawException(xN +5 , Ycontrol + 4)
				elif PAIR_INFO_ORPHAN == item[idNote]:
					fillRGB(colorKRN)
					drawException(xN +5, Ycontrol + 4)
					drawException(xN + 10 +5, Ycontrol + 4)
				elif PAIR_INFO_ATTENTION == item[idNote]:
					text(chr(int('25CB',16)), (xN + 6, Ycontrol + 3))
				elif PAIR_INFO_EMPTY == item[idNote]:
					fillRGB(COLOR_KERN_VALUE_NEGATIVE)
					if selected:
						# colorKRN = (1,.2,.2,1)
						fillRGB((1,.2,.2,1))
					text(chr(int('2716', 16)), (xN + 3 +5, Ycontrol + 3))
				# else:
				# 	text(item['note'], (xN , Ycontrol + 3))  # item['idx']+
				# fillRGB(COLOR_GREY_20)


				if self._previewGlyph:
					scalefactor = .030  # .05
					if PAIR_INFO_EMPTY == item[idNote]:
						fillRGB(COLOR_KERN_VALUE_NEGATIVE)
						font(self._viewFontName, fontSize = self._viewFontSize + 20)
						_xe, _ye = textSize(chr(int('2716', 16)))
						text(chr(int('2716', 16)), (xRp - _xe/2 , Ycontrol + 4))
						font(self._viewFontName, fontSize = self._viewFontSize)
					else:
						glyphL = self.font[item[idGlyphL]]
						glyphR = self.font[item[idGlyphR]]

						fillRGB(COLOR_BLACK)
						if checkOverlapingGlyphs(self.font, glyphL, glyphR, item[idKern]):
							fillRGB(COLOR_KERN_VALUE_NEGATIVE)
						save()

						translate(xRp - glyphL.width * scalefactor - (item[idKern] / 2) * scalefactor, Ycontrol + 12)
						scale(scalefactor)
						penL = CocoaPen(self.font)
						glyphL.draw(penL)
						drawPath(penL.path)
						restore()

						save()
						translate(xRp + (item[idKern] / 2) * scalefactor, Ycontrol + 12)
						scale(scalefactor)
						penR = CocoaPen(self.font)
						glyphR.draw(penR)
						drawPath(penR.path)
						restore()


				# TODO когда режим Селекции попробовать разделять каждый столбец по глифам
				if idx+1<len(self._viewArray):

					if True: #self._viewingMode == idModeShowAll:
						colorStroke = COLOR_GREY_20
						colorSeparate = COLOR_GREY_30
						if self.darkmode == True:
							colorStroke = ((.07,.07,.07,1))
							colorSeparate = ((.3,.3,.3,1))

						fillRGB(colorStroke)
						if self._sortName == 'left':
							if item[idDispL] != self._viewArray[idx+1][idDispL]:
								fillRGB(colorSeparate)
								rect(Xpos, Ycontrol, visibleWidth, 1)
						if self._sortName == 'right':
							if item[idDispR] != self._viewArray[idx+1][idDispR]:
								fillRGB(colorSeparate)
								rect(Xpos, Ycontrol, visibleWidth, 1)
						if self._sortName == 'values':
							if item[idKern] != self._viewArray[idx+1][idKern]:
								fillRGB(colorSeparate)
								rect(Xpos, Ycontrol, visibleWidth, 1)
						if self._sortName == 'notes':
							if item[idNote] != self._viewArray[idx+1][idNote]:
								fillRGB(colorSeparate)
								rect(Xpos, Ycontrol, visibleWidth, 1)
						rect(Xpos, Ycontrol, visibleWidth, 1)
					# else:
					# 	fillRGB(COLOR_GREY_20)
					# 	if item[idDispL] != self._viewArray[idx + 1][idDispL]:
					# 		fillRGB(COLOR_GREY_30)
					# 		rect(Xpos, Ycontrol, xR, 1)
					# 	else:
					# 		fillRGB(COLOR_GREY_20)
					# 		rect(Xpos, Ycontrol, xR, 1)
					#
					# 	if item[idDispR] != self._viewArray[idx + 1][idDispR]:
					# 		fillRGB(COLOR_GREY_30)
					# 		rect(xR, Ycontrol, xR, 1)
					# 	else:
					# 		fillRGB(COLOR_GREY_20)
					# 		rect(xR, Ycontrol, xR, 1)
					# 	if item[idKern] != self._viewArray[idx + 1][idKern]:
					# 		fillRGB(COLOR_GREY_30)
					# 		rect(xV, Ycontrol, wValue, 1)
					# 	else:
					# 		fillRGB(COLOR_GREY_20)
					# 		rect(xV, Ycontrol, wValue, 1)
					# 	if item[idNote] != self._viewArray[idx + 1][idNote]:
					# 		fillRGB(COLOR_GREY_30)
					# 		rect(xN, Ycontrol, wNote, 1)
					# 	else:
					# 		fillRGB(COLOR_GREY_20)
					# 		rect(xN, Ycontrol, wNote, 1)


					# 	if self._sortName != 'right' and item[idDispL] != self._viewArray[idx+1][idDispL]:
					# 		fillRGB(COLOR_GREY_30)
					# 		rect(Xpos, Ycontrol, visibleWidth, 1)
					#
					#
					# 	elif self._sortName != 'left' and item[idDispR] != self._viewArray[idx+1][idDispR]:
					# 		fillRGB(COLOR_GREY_30)
					# 		rect(Xpos, Ycontrol, visibleWidth, 1)
					#
					# 	if item[idDispR] != self._viewArray[idx + 1][idDispR]:
					# 		fillRGB(COLOR_GREY_20)
					# 		rect(xR, Ycontrol, xR, 1)
					# 	if item[idDispL] != self._viewArray[idx + 1][idDispL]:
					# 		fillRGB(COLOR_GREY_20)
					# 		rect(Xpos, Ycontrol, xR, 1)

			Ypos += self._lineSize
		restore()
		# self.updateStatusbar()



# TEST Section
# if __name__ == "__main__":
import os
import sys

def saveKerning (font, selectedkern, filename):
	print('=' * 60)
	print(font.info.familyName, font.info.styleName)
	print('Saving kerning to file:')
	fn = filename
	print(fn)
	groupsfile = open(fn, mode = 'w')
	txt = ''
	for (l, r) in sorted(selectedkern):
		txt += '%s %s %s\n' % (l, r, str(font.kerning[(l, r)]))
	groupsfile.write(txt)
	groupsfile.close()
	print(len(selectedkern), 'pairs saved..')
	print('Done.')


def loadKernFile (font, filename, mode='replace'):  # replace / add
	fn = filename
	if os.path.exists(fn):
		print('=' * 60)
		print(font.info.familyName, font.info.styleName)
		print('Loading kerning from file:')
		print(fn)
		f = open(fn, mode = 'r')
		pairsbefore = len(font.kerning)
		pairsimported = 0
		for line in f:
			line = line.strip()
			if not line.startswith('#') and line != '':
				left = line.split(' ')[0]
				right = line.split(' ')[1]
				value = int(round((float(line.split(' ')[2])), 0))
				fl = False
				fr = False
				if left in font.groups:
					fl = True
				if left in font:
					fl = True
				if right in font.groups:
					fr = True
				if right in font:
					fr = True
				if fl and fr:
					font.kerning[(left, right)] = value
					pairsimported += 1
				else:
					print('Group or Glyph not found:', left, right, value)

		f.close()
		print('Kerning loaded..')
		print('pairs before:\t', pairsbefore)
		print('pairs imported:\t', pairsimported)
		print('total pairs:\t', len(font.kerning))
	else:
		print('ERROR! kerning file not found')


class TDKernFinger(BaseWindowController):
	def __init__ (self):
		self.w = Window((350, 600), "KernFinger", minSize = (200, 100))
		# self.w.getNSWindow().setBackgroundColor_(NSColor.controlAccentColor())

		menuH = 17
		sepH = 5
		self.modeShowAll = True
		self.previewMode = False
		self.filterMode = idFilterBoth
		self.pairsPerLine = 4
		self.sendMode = 'groupped'
		self.observerID = getUniqName()

		self.w.menuMain = TDControlPanel((5, sepH, -5, 17),  # -160
		                              parentWindow = self)
		self.w.menuMain.addControlItem(title = 'select font', callback = self.fontMenuCall)
		self.w.menuMain.addMenuSeparator()
		self.w.menuMain.addControlItem(title = 'append from file', callback = self.appendKernFromFile)
		self.w.menuMain.addMenuSeparator()
		self.w.menuMain.addControlItem(title = 'save to file', callback = self.saveSelectedPairs2file)

		self.w.menuFilters = TDControlPanel((5, sepH + menuH + sepH, -5, 17),  # -160
	                                      parentWindow = self)
		self.swShowMode = self.w.menuFilters.addSwitchControlItem(switchers = (('all pairs','all'),
		                                                                       ('from selection','selection')),
		                                                          callback = self.modeShowSelectionCallback)
		self.w.menuFilters.setSwitchItem(self.swShowMode, switch = 'all pairs')
		self.w.menuFilters.addMenuSeparator()

		self.filterSide = self.w.menuFilters.addSwitchControlItem(switchers = (('side1',idFilterSide1),
		                                                                        ('both',idFilterBoth),
		                                                                        ('side2',idFilterSide2)),
		                                                          callback = self.modeFiltersSelectionCallback)
		self.w.menuFilters.setSwitchItem(self.filterSide,'both')
		self.w.menuFilters.enableControlItem(self.filterSide, False)
		self.w.menuFilters.addMenuSeparator()

		self.lblpreview = self.w.menuFilters.addControlItem(title = chr(int('1F170', 16)) + chr(int('1F185', 16)),  # 1F170 1F185
		                                            callback = self.setPreviewMode)

		self.w.kernlistControl = TDKernListControl((5, sepH + menuH + sepH + menuH + 2 ,-5,17),
		                                           selectionCallback = self.kernListControlCalback)
		self.w.kernlist = TDKernListView((5,sepH + menuH + sepH + menuH +  menuH +1,-5,-130 + 41), # 130
		                                 selectionCallback = self.KLselectionCallback,
		                                 commandCallback = self.commandsKernListCallback,
		                                 window = self.w)

		self.w.g = Group((0,-128 + 41,-0,100)) # 128
		self.w.g.menuOperation = TDControlPanel((5, 0, -5, 17),  # -160
		                              parentWindow = self)
		self.w.g.menuOperation.addControlItem(title = 'delete',
		                            hotkey = chr(int('232B', 16)),
		                            command = COMMAND_DELETE_PAIR,
		                            callback = self.deleteSelectedPairsCallback)
		self.w.g.menuOperation.addControlItem(title = 'send to KernTool',
		                            hotkey = 'space',
		                            command = COMMAND_SPACEKEY,
		                            callback = self.w.kernlist.prepare4sendSelectedPairsToKernTool)

		# width 380 -5 +5 margins
		# reserved 30
		# 380 - 10 -30 /2 = 175 width of EditText
		# xlbl = 5+ 150 = 155
		# x2edit = 155 + 30
		Yctrl = 19 # 60
		ww = 350
		margins = 5
		wlbl = 30
		wedit = (ww - margins*2 - wlbl) /2
		xlbl = margins + wedit
		x2edit = wedit + wlbl + margins
		self.w.g.preEdit = EditText((5, Yctrl, wedit, 17),text = '/H/H', sizeStyle = 'small')
		self.w.g.preEdit.getNSTextField().setBordered_(False)
		# self.w.g.preEdit.getNSTextField().setFont_(NSFont.fontWithName_size_('.SFCompactText-Regular', 12))
		self.w.g.lbl = TextBox((xlbl,Yctrl+4,wlbl,17),'_::_',sizeStyle = 'small', alignment = 'center')
		self.w.g.postEdit = EditText((x2edit, Yctrl, wedit, 17), text = '/n/n/o/o',sizeStyle = 'small')
		self.w.g.postEdit.getNSTextField().setBordered_(False)
		# self.w.g.postEdit.getNSTextField().setFont_(NSFont.fontWithName_size_('.SFCompactText-Regular', 12))


		self.w.g.menuPairsCount = TDControlPanel((5, Yctrl + 19, -5, 17),  # -160
		                                parentWindow = self )
		self.swgrp = self.w.g.menuPairsCount.addSwitchControlItem(switchers = (('groupped','groupped'),
		                                                                       ('expanded','expanded')),
		                                                          callback = self.switchSend2KTCallback)
		self.w.g.menuPairsCount.setSwitchItem(self.swgrp, switch = 'groupped')
		self.w.g.menuPairsCount.addMenuSeparator()

		self.swpairs = self.w.g.menuPairsCount.addSwitchControlItem(switchers = (('1',1),
		                                                          ('2',2),
		                                                          ('3',3),
		                                                          ('4',4),
		                                                          ('pairs/line',5)),
		                                             callback = self.switchPairsPerLineCallback)
		self.w.g.menuPairsCount.setSwitchItem(self.swpairs,'4')

		self.w.menuStatusBar = TDControlPanel((5, -27, -5, 17),  # -160
		                                parentWindow = self,
		                                selectionCallback = None,
		                                keyPressedCallback = None,
		                                active = False )

		self.w.labelTotalPairsID = self.w.menuStatusBar.addLabelItem(title = 'pairs', value = 0)
		self.w.menuStatusBar.addMenuSeparator(type = ' ')
		self.w.labelShowedPairsID = self.w.menuStatusBar.addLabelItem(title = 'shown', value = 0)
		self.w.menuStatusBar.addMenuSeparator(type = ' ')
		self.w.labelSelectedPairsID = self.w.menuStatusBar.addLabelItem(title = 'selected', value = 0)

		self.w.kernlistControl.setupControl({'title':' ','name':'left'},
		                                    {'title':' ','name':'right'},
		                                    {'title':'','name':'value'},
		                                    {'title':'','name':'note'}) # chr(int('21B9',16))

		self.font = CurrentFont()
		self.fontID = getFontID(self.font)
		self.w.kernlist.setFont(self.font)
		self.hashKernDic = TDHashKernDic(self.font)
		self.w.setTitle(title = 'KernFinger: %s %s' % (self.font.info.familyName, self.font.info.styleName))
		self.w.kernlist.setViewingMode(mode = self.modeShowAll,
		                               sorting = 'left', reverse = False, filterMode = self.filterMode)
		self.w.kernlistControl.selectMenuItem('left', reversed = False)

		self.leftReverse = False
		self.rightReverse = False
		self.valuesReverse = False
		self.notesReverse = False

		self.sortName = None

		addObserver(self, "glyphChanged", "currentGlyphChanged")
		addObserver(self, 'refreshKernView', EVENT_REFRESH_ALL_OBSERVERS)

		# self.w.bind('close', self.windowCloseCallback)
		self.w.bind('resize', self.widwowResize)
		self.setUpBaseWindowBehavior()

		self.w.open()
		self.w.kernlist.scrollToLine(0)

	def windowCloseCallback (self, sender):
		removeObserver(self, "currentGlyphChanged")
		removeObserver(self, EVENT_REFRESH_ALL_OBSERVERS)
		# super(MyW, self).windowCloseCallback(sender)
		# print('KernFinger: DONE.')

	def widwowResize (self, sender):
		x,y, w, h = sender.getPosSize()
		# print (posSize)
		Yctrl = 19  # 60
		# ww = 320
		ww = w
		margins = 5
		wlbl = 30
		wedit = (ww - margins * 2 - wlbl) / 2
		xlbl = margins + wedit
		x2edit = wedit + wlbl + margins
		self.w.g.preEdit.setPosSize((5,Yctrl, wedit, 17))
		self.w.g.lbl.setPosSize((xlbl, Yctrl+4, wlbl, 17))
		self.w.g.postEdit.setPosSize((x2edit, Yctrl, wedit, 17))
		self.w.menuMain.updatePanel()
		self.w.menuStatusBar.updatePanel()
		self.w.g.menuPairsCount.updatePanel()
		self.w.menuFilters.updatePanel()
		self.w.kernlist.updatePanel()
		self.w.kernlistControl.updatePanel()
		self.w.g.menuOperation.updatePanel()


	def refreshKernView(self, info):
		if info['fontID'] == self.fontID and info['observerID'] != self.observerID:
			self.w.kernlist.refreshKernPair(info['pair'])

	def glyphChanged(self, info):
		self.w.kernlist.refreshView(fullrefresh = False)

	def deleteSelectedPairsCallback(self):
		pairs = self.w.kernlist.getListOfSelectedPairs()
			# print('deleting pairs:')
		if pairs:
			for pair in pairs:
				# print (pair)
				if pair in self.font.kerning:
					self.font.kerning.remove(pair)
					self.w.kernlist.refreshKernPair(pair)
			postEvent(EVENT_REFRESH_ALL_OBSERVERS, fontID = self.fontID, observerID = self.observerID)


	def modeShowSelectionCallback(self, command):
		if command == 'all':
			self.modeShowAll = True
			self.w.kernlist.setViewingMode(idModeShowAll)
			self.w.menuFilters.enableControlItem(self.filterSide, False)
		elif command == 'selection':
			self.modeShowAll = False
			self.w.kernlist.setViewingMode(idModeSelected, filterMode = self.filterMode)
			self.w.menuFilters.enableControlItem(self.filterSide, True)

	def modeFiltersSelectionCallback(self, command):
		self.filterMode = command
		self.w.kernlist.setViewingMode(idModeSelected, filterMode = self.filterMode)


	def switchSend2KTCallback(self, mode):
		self.sendMode = mode


	def switchPairsPerLineCallback(self, mode):
		self.pairsPerLine = mode

	def commandsKernListCallback(self, info):
		if info['command'] == COMMAND_SPACEKEY:
			self.sendPairsToKernTool(info)
		elif info['command'] == COMMAND_DELETE_PAIR:
			self.deleteSelectedPairsCallback()


	def sendPairsToKernTool(self, info):
		patternLeft = tdGlyphparser.translateText(font = self.font,
		                                               text = self.w.g.preEdit.get())
		patternRight = tdGlyphparser.translateText(font = self.font,
		                                                text = self.w.g.postEdit.get())
		LPattern = ''
		RPattern = ''
		if patternLeft:
			for l in patternLeft:
				if l != '':
					LPattern += '/%s' % l
		if patternRight:
			for r in patternRight:
				if r != '':
					RPattern += '/%s' % r
		cl = None
		cr = None
		if self.sendMode == 'groupped':
			line =''
			count = 0
			ppl = self.pairsPerLine
			for idx, (l,r) in enumerate(info['pairs']):
				if idx == 0:
					cl = l
					cr = r
				line += '%s/%s/%s%s' % (LPattern, l ,r ,RPattern)
				count +=1
				if ppl !=5 and count == ppl:
					line += '\\n'
					count = 0
		else:
			line = ''
			count = 0
			ppl = self.pairsPerLine
			listL = []
			listR = []
			for idx, (l,r) in enumerate(info['pairs']):
				if idx == 0:
					cl = l
					cr = r
				gl = self.hashKernDic.getGroupNameByGlyph(l,'L')
				gr = self.hashKernDic.getGroupNameByGlyph(r,'R')

				if gl.startswith(ID_KERNING_GROUP):
					for kl in self.font.groups[gl]:
						if gr.startswith(ID_KERNING_GROUP):
							for kr in self.font.groups[gr]:
								line += '%s/%s/%s%s' % (LPattern, kl, kr, RPattern)
								count += 1
								if ppl != 5 and count == ppl:
									line += '\\n'
									count = 0
						else:
							line += '%s/%s/%s%s' % (LPattern, kl, r, RPattern)
							count += 1
							if ppl != 5 and count == ppl:
								line += '\\n'
								count = 0
				else:
					if gr.startswith(ID_KERNING_GROUP):
						for kr in self.font.groups[gr]:
							line += '%s/%s/%s%s' % (LPattern, l, kr, RPattern)
							count += 1
							if ppl != 5 and count == ppl:
								line += '\\n'
								count = 0
					else:
						line += '%s/%s/%s%s' % (LPattern, l, r, RPattern)
						count += 1
						if ppl != 5 and count == ppl:
							line += '\\n'
							count = 0

			# s = ''
			# for i, l in enumerate(listL):
			# 	line += '%s/%s/%s%s' % (LPattern, l, listR[i], RPattern)
			# 	count += 1
			# 	if ppl != 5 and count == ppl:
			# 		line += '\\n'
			# 		count = 0

		# print (line)
		postEvent('typedev.KernTool.observerSetText',
		          glyphsLine = line,
		          glyphsready = True,
		          targetpair = (cl,cr),
		          fontID = getFontID(self.font),
		          # observerID = self.observerID)
		          )

	def saveSelectedPairs2file(self):
		pairsfile = putFile(messageText = 'Save selected pairs to text file', title = 'title')
		if pairsfile:
			pairs = self.w.kernlist.getListOfSelectedPairs()
			saveKerning(self.font, pairs, pairsfile)

	def appendKernFromFile(self):
		pairsfile = getFile(messageText = 'Append pairs from file', title = 'title')
		if pairsfile:
			loadKernFile(self.font, pairsfile[0])
			self.w.kernlist.setFont(self.font)
			self.hashKernDic = TDHashKernDic(self.font)

			self.w.kernlist.setViewingMode(mode = self.modeShowAll, sorting = 'left', reverse = False)
			self.w.kernlistControl.selectMenuItem('left', reversed = False)
			# for (l,r), v in sorted(self.font.kerning.items()):
			# 	self.w.kernlist.addItem({'left':l,'right':r,'value':v,'note':'what the fuck are you doing?!'})

			self.leftReverse = False
			self.rightReverse = False
			self.valuesReverse = False
			self.notesReverse = False

			self.sortName = None


	def kernListControlCalback(self, info):
		if info == 'left':
			self.sortName = info
			self.w.kernlistControl.selectMenuItem(info, reversed = self.leftReverse)
			self.w.kernlist.setViewingMode(mode = self.modeShowAll,
			                               sorting = 'left', reverse = self.leftReverse, filterMode = self.filterMode)
			self.w.kernlist.scrollToLine(0)
			self.leftReverse = not self.leftReverse
			self.rightReverse = False
			self.valuesReverse = False
			self.notesReverse = False
		elif info == 'right':
			self.sortName = info
			self.w.kernlistControl.selectMenuItem(info, reversed = self.rightReverse)
			self.w.kernlist.setViewingMode(mode = self.modeShowAll,
			                               sorting = 'right', reverse = self.rightReverse, filterMode = self.filterMode)
			self.w.kernlist.scrollToLine(0)
			self.leftReverse = False
			self.rightReverse = not self.rightReverse
			self.valuesReverse = False
			self.notesReverse = False
		elif info == 'value':
			self.sortName = info
			self.w.kernlistControl.selectMenuItem(info, reversed = self.valuesReverse)
			self.w.kernlist.setViewingMode(mode = self.modeShowAll,
			                               sorting = 'values', reverse = self.valuesReverse, filterMode = self.filterMode)
			self.w.kernlist.scrollToLine(0)
			self.leftReverse = False
			self.rightReverse = False
			self.valuesReverse = not self.valuesReverse
			self.notesReverse = False
		elif info == 'note':
			self.sortName = info
			self.w.kernlistControl.selectMenuItem(info, reversed = self.notesReverse)
			self.w.kernlist.setViewingMode(mode = self.modeShowAll,
			                               sorting = 'notes', reverse = self.notesReverse, filterMode = self.filterMode)
			self.w.kernlist.scrollToLine(0)
			self.leftReverse = False
			self.rightReverse = False
			self.valuesReverse = False
			self.notesReverse = not self.notesReverse


	def setPreviewMode(self):
		self.previewMode = not self.previewMode
		self.w.menuFilters.setStateItem(self.lblpreview, self.previewMode)
		self.w.kernlist.setPreviewMode(self.previewMode)


	def KLselectionCallback(self, info):
		pass

	def fontMenuCall (self):
		from mojo.UI import SelectFont
		font = SelectFont(title='KernFinger')
		self.changeFont(font)
		# MenuDialogWindow(parentWindow = self.w, callback = self.changeFont)

	def changeFont(self, font):
		if not font:
			self.font = CurrentFont()
		else:
			self.font = font
		self.fontID = getFontID(self.font)
		self.w.kernlist.setFont(self.font)
		self.hashKernDic = TDHashKernDic(self.font)
		self.w.setTitle(title = 'KernFinger: %s %s' % (self.font.info.familyName, self.font.info.styleName))
		self.w.kernlist.setViewingMode(mode = self.modeShowAll, sorting = 'left', reverse = False)
		self.w.kernlistControl.selectMenuItem('left', reversed = False)

		self.leftReverse = False
		self.rightReverse = False
		self.valuesReverse = False
		self.notesReverse = False

		self.sortName = None

		self.w.kernlist.scrollToLine(0)


	# MyW()
