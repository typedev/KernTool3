# -*- coding: utf-8 -*-

import sys
# from math import *
from vanilla import *
from mojo.UI import *
from fontParts.world import CurrentFont, RGlyph
from defconAppKit.windows.baseWindow import BaseWindowController
from mojo.canvas import Canvas
from mojo.drawingTools import *
from mojo.glyphPreview import GlyphPreview
from defconAppKit.controls.glyphCollectionView import GlyphCollectionView
from AppKit import *
# from mojo.drawingTools import drawingTools
from fontTools.pens.cocoaPen import CocoaPen

import importlib

import tdCanvasKeysDecoder
importlib.reload(tdCanvasKeysDecoder)
from tdCanvasKeysDecoder import decodeCanvasKeys
from mojo.canvas import Canvas

from mojo.drawingTools import *
# from robofab.world import CurrentFont
# from vanilla.nsSubclasses import getNSSubclass
from defconAppKit.windows import *

import tdKernToolEssentials

importlib.reload(tdKernToolEssentials)
from tdKernToolEssentials import *

import tdGroupViews

importlib.reload(tdGroupViews)
from tdGroupViews import TDGroupLine


class TDExceptionLine(VanillaBaseObject):
	nsViewClass = NSView

	def __init__ (self, posSize, selectionCallback=None, sizeStyle='big'):
		xw, yw, tx, ty = posSize
		self.glyphsToDisplay = []
		self.keyGlyph = None
		self.font = None

		self.hashKernDic = None
		self.direction = 'L'
		self.showSelected = False
		self.groupIsEmpty = False
		self.diffMarginsInGroup = False
		self.groupname = None
		self.keyGlyph = None
		self.keyGlyphMargin = None
		self.showInfo = True

		self.excGlyphL = None
		self.excGlyphR = None
		self.kernValue = 0

		self.darkmode = KERNTOOL_UI_DARKMODE
		self.darkmodeWarm = KERNTOOL_UI_DARKMODE_WARMBACKGROUND

		self._alpha = .1
		self._scalefactorUI = .045  # sizeStyle = 'regular'
		ty = 85
		if sizeStyle == 'big':
			self._scalefactorUI = .065
			ty = 100
		elif sizeStyle == 'small':
			self._scalefactorUI = .035
			ty = 65
		elif sizeStyle == 'mini':
			self._scalefactorUI = .025
			ty = 45
		elif sizeStyle == 'micro':
			self._scalefactorUI = .015
			ty = 30
		self.heightOfControl = ty

		self._selectionCallback = selectionCallback

		self._selfHeight = ty
		self._setupView(self.nsViewClass, (xw, yw, tx, ty))  # (0, 0, -0, 106)
		self.infoLine = Canvas((0, 0, -0, -0),
		                       delegate = self,  # canvasSize = (ty, ty),
		                       hasHorizontalScroller = False,
		                       hasVerticalScroller = False,
		                       autohidesScrollers = True,
		                       backgroundColor = NSColor.whiteColor(),
		                       # acceptMouseMoved = True
		                       )
		self.infoLine.scrollView.getNSScrollView().setBorderType_(NSNoBorder)
		# self.infoLine.update()

	def setFont (self, font, hashKernDic):
		self.font = font
		self.hashKernDic = hashKernDic

	def selected (self, selected=False):
		self.showSelected = selected
		self.infoLine.update()
		# if self._selectionCallback and selected:
		# 	self._selectionCallback(self)

	def setKeyGlyph (self, groupname):
		if len(self.font.groups[groupname]) > 0:
			gname = self.font.groups[groupname][0]
			self.keyGlyph = gname
		else:
			self.keyGlyph = None
			self.keyGlyphMargin = 0
			self.groupIsEmpty = True

	def setupGroupView (self, groupname):
		self.glyphsToDisplay = []
		self.diffMarginsInGroup = False
		self.groupname = groupname
		self.setKeyGlyph(groupname = groupname)
		if not self.keyGlyph: return

		totalglyphs = len(self.font.groups[groupname])
		if totalglyphs in range(0, 6):
			self._alpha = .3
		else:
			self._alpha = .1
		for idx, glyphname in enumerate(self.font.groups[groupname]):
			if glyphname in self.font:
				self.glyphsToDisplay.append(self.font[glyphname])
		self.infoLine.update()

	def setPair (self, pair, direction):

		self.direction = direction
		l, r = pair
		pair = researchPair(self.font, self.hashKernDic, (l, r))
		self.excPairName = (l, r)
		gL = pair['L_nameForKern']
		gR = pair['R_nameForKern']
		if not pair['kernValue']:
			self.kernValue = 0
		else:
			self.kernValue = pair['kernValue']

		if self.direction == 'L':
			self.resultPair = (gL, r)
			self.setupGroupView(gL)

		elif self.direction == 'R':
			self.resultPair = (l, gR)
			self.setupGroupView(gR)

		elif self.direction == 'B':
			self.resultPair = (l, r)
			self.infoLine.update()


	def mouseDown (self, event):
		if self._selectionCallback:
			self._selectionCallback(self)

	def resetView (self):
		self.infoLine.update()

	def draw (self):
		def drawLeftCursor (txt, Xcenter, Ycontrol, color):
			m = 17
			y = Ycontrol
			fsize = 10
			step = 0 # 6.55
			font('Menlo', fsize * m)
			fill(0, 0, 0, 1)
			txlen, _y = textSize(txt)
			if color:
				fillRGB(COLOR_EXCEPTION_GROUP_ICON)
			# w = step * len(txt) * m + step * m
			w = txlen + 140
			Xpos = Xcenter - w + 20
			newPath()
			moveTo((Xpos, y))
			curveTo((Xpos - 7 * m, y), (Xpos - 7 * m, y + 2 * m), (Xpos - 7 * m, y + 7 * m))
			curveTo((Xpos - 7 * m, y + 12 * m), (Xpos - 7 * m, y + 14 * m), (Xpos, y + 14 * m))
			# lineTo((Xpos + w, y + 14 * m))

			lineTo((Xpos + w, y + 14 * m))
			lineTo((Xpos + w - 3 * m, y + 7 * m))
			lineTo((Xpos + w, y + 7 * m))
			lineTo((Xpos + w - 3 * m, y))

			lineTo((Xpos + w, y))
			closePath()
			drawPath()

			fill(1, 1, 1, 1)
			text(txt, (Xpos, y + 1.5 * m))

		def drawRightCursor (txt, Xcenter, Ycontrol, color):
			m = 17
			y = Ycontrol
			fsize = 10
			step = 0 #6.55
			font('Menlo', fsize * m)
			fill(0, 0, 0, 1)
			txlen, _y = textSize(txt)

			if color:
				fillRGB(COLOR_EXCEPTION_GROUP_ICON)
			# w2 = step * len(txt) * m + (step / 2) * m + step * m
			w2 = txlen + 140
			Xpos = Xcenter - 20
			w = 0
			newPath()
			moveTo((Xpos + w, y))
			# lineTo((Xpos + w, y + 14 * m))

			lineTo((Xpos + 3 * m, y + 7 * m))
			lineTo((Xpos, y + 7 * m))
			lineTo((Xpos + 3 * m, y + 14 * m))

			lineTo((Xpos + w + w2, y + 14 * m))
			curveTo((Xpos + w + w2 + 7 * m, y + 14 * m), (Xpos + w + w2 + 7 * m, y + 12 * m),
			        (Xpos + w + w2 + 7 * m, y + 7 * m))
			curveTo((Xpos + w + w2 + 7 * m, y + 2 * m), (Xpos + w + w2 + 7 * m, y), (Xpos + w + w2, y))
			closePath()
			drawPath()
			fill(1, 1, 1, 1)
			text(txt, (Xpos + w + step * m + 140, y + 1.5 * m))

		visibleHeight = self.infoLine.scrollView.getNSScrollView().documentVisibleRect().size.height
		visibleWidth = self.infoLine.scrollView.getNSScrollView().documentVisibleRect().size.width

		scalefactor = self._scalefactorUI
		Xcenter = visibleWidth / 2

		# if not self.glyphsToDisplay: return

		if self.keyGlyph:
			keyGlyph = self.font[self.keyGlyph]  # self.glyphsToDisplay[-1]
			keyWidth = keyGlyph.width
		else:
			keyWidth = 0
		Xright = 0
		Xleft = Xcenter  # - keyWidth/2
		Xright = Xleft  # + keyWidth

		if self.darkmodeWarm:
			fillRGB((.75, .73, .7, .8))
			# _rw = self.maxX+100
			# # print('maxY', maxY)
			# if _rw < visibleWidth:
			# 	_rw = visibleWidth #+ 500
			rect(0, 0, visibleWidth, visibleHeight)

		translate(visibleWidth / 2 - visibleWidth / 30, (visibleHeight / 3))  # -4

		stroke(0, 0, 0, 0)
		strokeWidth(0)
		scale(scalefactor)

		if self.direction != 'B':
			for idx, glyph in enumerate(self.glyphsToDisplay):
				save()
				pen = CocoaPen(self.font)
				if self.direction == 'L':
					translate(Xcenter - glyph.width, 0)
				elif self.direction == 'R':
					translate(self.kernValue + Xcenter, 0)
				fill(0, 0, 0, self._alpha)
				if glyph.name == self.keyGlyph:
					fill(0, 0, 0, 1)
				glyph.draw(pen)
				drawPath(pen.path)

				restore()
				translate(0, 0)

			save()
			(l, r) = self.resultPair
			pen = CocoaPen(self.font)
			if self.direction == 'L':
				glyph = self.font[r]
				translate(self.kernValue + Xcenter, 0)
			elif self.direction == 'R':
				glyph = self.font[l]
				translate(Xcenter - glyph.width, 0)
			fillRGB(COLOR_EXCEPTION_GROUP_ICON)
			glyph.draw(pen)
			drawPath(pen.path)
			restore()
			translate(0, 0)

		elif self.direction == 'B':
			save()
			(l, r) = self.resultPair
			pen = CocoaPen(self.font)
			glyph = self.font[l]
			translate(Xcenter - glyph.width, 0)
			fillRGB(COLOR_EXCEPTION_GROUP_ICON)
			glyph.draw(pen)
			drawPath(pen.path)
			restore()
			translate(0, 0)
			save()
			pen = CocoaPen(self.font)

			glyph = self.font[r]
			translate(self.kernValue + Xcenter, 0)
			fillRGB(COLOR_EXCEPTION_GROUP_ICON)
			glyph.draw(pen)
			drawPath(pen.path)
			restore()
			translate(0, 0)

		if self.showSelected:
			Ycontrol = -450
			(l, r) = self.resultPair
			if self.direction == 'L':
				drawLeftCursor(getDisplayNameGroup(l),Xcenter-20, Ycontrol,False)
				drawRightCursor(r, Xcenter+20,Ycontrol,True)
			elif self.direction == 'R':
				drawLeftCursor(l, Xcenter-20, Ycontrol, True)
				drawRightCursor(getDisplayNameGroup(r), Xcenter+20, Ycontrol, False)
			elif self.direction == 'B':
				drawLeftCursor(l, Xcenter-20, Ycontrol, True)
				drawRightCursor(r, Xcenter+20, Ycontrol, True)

		self.infoLine._view.setFrame_(NSMakeRect(0, 0, visibleWidth, visibleHeight))



class TDExceptionView(object):
	def __init__ (self, parentWindow, font=None,
	              hashKernDic=None, pair=None, callback=None, autokern = True):
		wW = 400
		hW = 500
		self.w = Sheet((wW, hW), parentWindow)
		self.callback = callback
		self.font = font
		self.hashKernDic = hashKernDic
		self.pair = pair

		self.selectedPair = None
		self.deltaKern = None
		self.useAutokern = autokern
		self.direction = 'L'

		hGRPcontrols = 85
		yInfoControl = 30

		sizeStyle = 'big'
		hasHorizontalScroller = False
		separatePairs = False
		# pair = ['T', 'icircumflex']
		self.w.lblMessage = TextBox((10, 10, -10, 17), text = 'Choose exception:', sizeStyle = 'small')

		self.w.gC = TDExceptionLine(posSize = (5, yInfoControl, -5, hGRPcontrols),
		                            selectionCallback = self._viewSelected,
		                            sizeStyle = sizeStyle)
		nextG = self.w.gC.heightOfControl
		self.w.gC2 = TDExceptionLine(posSize = (5, yInfoControl + nextG + 2, -5, hGRPcontrols),
		                             selectionCallback = self._viewSelected,
		                             sizeStyle = sizeStyle)
		nextG += self.w.gC2.heightOfControl
		self.w.gC3 = TDExceptionLine(posSize = (5, yInfoControl + nextG + 4, -5, hGRPcontrols),
		                             selectionCallback = self._viewSelected,
		                             sizeStyle = sizeStyle)

		nextG += self.w.gC3.heightOfControl + 8

		self.w.lblMessage2 = TextBox((10, yInfoControl + nextG, 200, 17), text = 'Preview:', sizeStyle = 'small')
		self.w.checkAutokern = CheckBox((-130, yInfoControl + nextG - 2, 140, 17),
		                                title = 'fix touches', value = self.useAutokern,
		                                sizeStyle = 'small', callback = self.checkUseAutokernCallback)
		self.w.checkAutokern.set(self.useAutokern)
		# self.deltaKern = self.getDeltaKern(self.pair)

		nextG = nextG + 16
		self.w.excPreview = TDGroupLine(posSize = (5, yInfoControl + nextG, -5, hGRPcontrols),
		                                # selectionCallback = self._viewSelected,
		                                separatePairs = True,
		                                sizeStyle = sizeStyle,
		                                hasHorizontalScroller = True,
		                                showValues = True)
		nextG += self.w.excPreview.heightOfControl

		self.w.gC.setFont(font, self.hashKernDic)
		self.w.gC.setPair(pair, direction = 'L')
		self.w.gC2.setFont(font, self.hashKernDic)
		self.w.gC2.setPair(pair, direction = 'R')
		self.w.gC3.setFont(font, self.hashKernDic)
		self.w.gC3.setPair(pair, direction = 'B')
		self.w.excPreview.setFont(font, self.hashKernDic)

		self.w.btnApply = Button(((wW / 2) + 2, yInfoControl + nextG + 8, -10, 17), "Apply",
		                         callback = self.btnCloseCallback,
		                         sizeStyle = 'small')
		self.w.btnCancel = Button((10, yInfoControl + nextG + 8, (wW / 2) - 12, 17), "Cancel",
		                          callback = self.btnCloseCallback,
		                          sizeStyle = 'small')

		self.w.open()
		self.w.gC.selected(True)
		if self.useAutokern:
			self.deltaKern = self.getDeltaKern(self.pair)
		self.w.excPreview.setPair(self.pair, direction = self.direction, deltaKern = self.deltaKern)
		self.selectedPair = self.w.gC.resultPair

	def _viewSelected (self, sender):
		# print 'info:', info
		# print sender#self.w.gC.get()
		# print sender.resultPair
		self.selectedPair = sender.resultPair
		if sender == self.w.gC:
			self.w.gC.selected(True)
			self.w.gC2.selected(False)
			self.w.gC3.selected(False)
			self.direction = 'L'
			self.w.excPreview.setPair(self.pair, direction = self.direction, deltaKern = self.deltaKern)

		elif sender == self.w.gC2:
			self.w.gC.selected(False)
			self.w.gC2.selected(True)
			self.w.gC3.selected(False)
			self.direction = 'R'
			self.w.excPreview.setPair(self.pair, direction = self.direction, deltaKern = self.deltaKern)
		elif sender == self.w.gC3:
			self.w.gC.selected(False)
			self.w.gC2.selected(False)
			self.w.gC3.selected(True)
			self.direction = 'B'
			self.w.excPreview.setPair(self.pair, direction = self.direction, deltaKern = self.deltaKern)

	def btnCloseCallback (self, sender):
		if self.callback and sender == self.w.btnApply:
			kern = self.deltaKern
			if not kern:
				kern = 0
			self.callback((self.selectedPair, kern, self.useAutokern))
		self.w.close()

	def checkUseAutokernCallback (self, sender):
		self.useAutokern = sender.get()
		if sender.get():
			self.deltaKern = self.getDeltaKern(self.pair)
			self.w.excPreview.setPair(self.pair, direction = self.direction, deltaKern = self.deltaKern)
		else:
			self.deltaKern = None
			self.w.excPreview.setPair(self.pair, direction = self.direction)

	def getDeltaKern (self, pair):
		return autoCalcPairValue(self.font, self.hashKernDic, self.pair, simplePair = True, mode = 'fixtouches')


# TEST Section
if __name__ == "__main__":
	class MyW(object):
		def __init__ (self):
			self.w = Window((300, 400), "Choose exception", minSize = (100, 100))
			hGRPcontrols = 85
			yInfoControl = 5
			wW = 500
			hW = 350
			self.font = CurrentFont()
			self.hashKernDic = TDHashKernDic(self.font)
			self.flagAutoKern = True
			self.pair = ['A', 'H']
			# self.pair = ['A', 'afii10071']
			# self.pair = ['Lslash', 'Tbar']


			self.w.btnOpen = Button(((wW / 2) + 2, hW - 22, -10, 17), "Apply", callback = self.btnOpenCallback,
			                        sizeStyle = 'small')

			self.w.open()

		def btnOpenCallback (self, sender):
			TDExceptionView(self.w, font = self.font,
			                hashKernDic = self.hashKernDic,
			                pair = self.pair,
			                callback = self.getResultFromexceptionView,
			                    autokern = self.flagAutoKern)

		def getResultFromexceptionView (self, result):
			(l,r), v, a = result
			print ('RESULT')
			print ((l,r),v,a)
			self.flagAutoKern = a


	MyW()
