# -*- coding: utf-8 -*-

import sys
# from math import *
from vanilla import *
from mojo.UI import *
import math
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
from tdCanvasKeysDecoder import decodeCanvasKeys, decodeModifiers
from mojo.canvas import Canvas


from mojo.drawingTools import *
# from robofab.world import CurrentFont
# from vanilla.nsSubclasses import getNSSubclass
from defconAppKit.windows import *

import tdKernToolEssentials
importlib.reload(tdKernToolEssentials)
from tdKernToolEssentials import *


class TDGroupViewStacked(VanillaBaseObject):
	nsViewClass = NSView

	def __init__ (self, posSize, selectionCallback=None, doubleClickCallback = None,
	              sizeStyle='regular', liveupdate=False):
		xw, yw, tx, ty = posSize
		self.glyphsToDisplay = []
		self.font = None

		self.hashKernDic = None
		self.direction = 'L'
		self.showSelected = False
		self.groupIsEmpty = False
		self.diffMarginsInGroup = False
		self.groupname = None
		self.keyGlyph = None
		self.keyGlyphMargin = None
		self.showMask = True
		self.showInfo = True
		self.imnotready = True
		self.liveupdate = liveupdate

		self.vertShift = 50

		self._alpha = .1
		self._scalefactorUI = .045  # sizeStyle = 'regular'
		ty = 85
		if sizeStyle == 'big':
			self._scalefactorUI = .065
			ty = 100
			self.vertShift = 0
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
		self._doubleClickCallbak = doubleClickCallback

		self.darkmode = KERNTOOL_UI_DARKMODE
		self.darkmodeWarm = KERNTOOL_UI_DARKMODE_WARMBACKGROUND

		self._selfHeight = ty
		self._setupView(self.nsViewClass, (xw, yw, tx, ty))  # (0, 0, -0, 106)
		self.infoLine = Canvas((0, 0, -0, -0),
		                       delegate = self,  # canvasSize = (ty, ty),
		                       hasHorizontalScroller = False,
		                       hasVerticalScroller = False,
		                       autohidesScrollers = True,

		                       # backgroundColor = NSColor.whiteColor(),
		                       # acceptMouseMoved = True
		                       )
		self.infoLine.scrollView.getNSScrollView().setBorderType_(NSNoBorder)
		self.infoLine.update()

	def setFont (self, font):
		self.font = font

		# self.glyphsToDisplay = []
		# self.infoLine.update()

	def selected (self, selected=False):
		self.showSelected = selected
		self.infoLine.update()

	def setKeyGlyph (self, groupname):
		if len(self.font.groups[groupname]) > 0:
			gname = self.font.groups[groupname][0]
			self.keyGlyph = gname
			self.keyGlyphMargin = getKeyGlyphMargin(self.font, keyglyph = gname, direction = self.direction)
			self.groupIsEmpty = False
		else:
			self.keyGlyph = None
			self.keyGlyphMargin = 0
			self.groupIsEmpty = True

	def setGroupStack (self, name, direction=None):
		# if self.groupname == name and not self.liveupdate: return
		if not direction:
			direction = getDirection(name)
		self.direction = direction
		self.glyphsToDisplay = []
		self.diffMarginsInGroup = False
		if ID_KERNING_GROUP in name:
			self.groupname = name
			self.setKeyGlyph(groupname = self.groupname)
			if not self.keyGlyph:
				self.imnotready = False
				self.infoLine.update()
				return

			totalglyphs = len(self.font.groups[self.groupname])
			if totalglyphs in range(0, 6):
				self._alpha = .3
			else:
				self._alpha = .1
			# self._alpha = (100/totalglyphs)/100 * len(self.font.groups[groupname])
			for idx, glyphname in enumerate(self.font.groups[self.groupname]):
				if glyphname in self.font:
					self.glyphsToDisplay.append(self.font[glyphname])
					if self.keyGlyphMargin != getKeyGlyphMargin(self.font, keyglyph = glyphname,
					                                            direction = direction):
						self.diffMarginsInGroup = True
		else:
			if name in self.font:
				self.keyGlyph = name
				self.keyGlyphMargin = getKeyGlyphMargin(self.font, keyglyph = name, direction = self.direction)
				self.glyphsToDisplay.append(self.font[name])
				self.groupname = name
				self.diffMarginsInGroup = False
		self.imnotready = False
		self.infoLine.update()

	def setupGroupViewExternal (self, groupname, glyphs, keyglyphname, margin, diffmargin, direction):
		# if self.groupname == groupname and not self.liveupdate: return
		self.groupname = groupname
		self.glyphsToDisplay = glyphs
		self.keyGlyph = keyglyphname
		self.keyGlyphMargin = margin
		self.diffMarginsInGroup = diffmargin
		self.direction = direction
		totalglyphs = len(glyphs)
		if totalglyphs in range(0, 6):
			self._alpha = .3
		else:
			self._alpha = .1
		self.imnotready = False
		self.infoLine.update()

	def mouseDown (self, event):

		if event.clickCount() == 2:
			if self._doubleClickCallbak:
				self._doubleClickCallbak(self.groupname)
		elif event.clickCount() == 1:
			if self._selectionCallback:
				self._selectionCallback(self.groupname)


	def draw (self):
		if self.imnotready: return
		stroke(0, 0, 0, 0)
		strokeWidth(0)
		font('Menlo', fontSize = 10)
		visibleHeight = self.infoLine.scrollView.getNSScrollView().documentVisibleRect().size.height
		visibleWidth = self.infoLine.scrollView.getNSScrollView().documentVisibleRect().size.width

		# self.infoLine._view.setFrame_(NSMakeRect(0, 0, visibleWidth, visibleHeight))

		def italicShift (angle, Ypos):
			if angle:
				italics_shift = Ypos * math.tan(abs(angle) * 0.0175)
				return italics_shift
			else:
				return 0

		if self.darkmodeWarm:
			fillRGB((.75, .73, .7, .8))
			# print('maxY', maxY)
			# if _rw < visibleWidth:
			# 	_rw = visibleWidth  # + 500
			rect(0, 0, visibleWidth, visibleHeight)

		scalefactor = self._scalefactorUI
		Xcenter = visibleWidth / 2
		if self.font:
			if self.groupIsEmpty: #not self.glyphsToDisplay:

				fillRGB(COLOR_KERN_VALUE_NEGATIVE)
				if self.showSelected:
					fill(.1, 0, 1, 1)
				rect(0, 0, visibleWidth, 15)
				fill(1)
				text(getDisplayNameGroup(self.groupname), (5, 1))
				return
			else:
				if self.keyGlyph:
					keyGlyph = self.font[self.keyGlyph]  # self.glyphsToDisplay[-1]
					keyWidth = keyGlyph.width
				else:
					keyWidth = 0
				Xright = 0
				Xleft = Xcenter - keyWidth / 2
				Xright = Xleft + keyWidth

				font('Menlo', fontSize = 9)

				if self.direction == 'L':
					if self.showMask:
						fill(.4)
						if self.font.info.italicAngle != 0:
							a = self.font.info.italicAngle
							h = visibleHeight
							w = visibleWidth
							polygon((0, 0), (0, h), (w / 2 + italicShift(a, h) / 2, h),
							        (w / 2 - italicShift(a, h) / 2, 0))
						else:
							rect(0, 0, (visibleWidth / 2), visibleHeight)
					fill(0, 0, 0, 1)
					shiftx = -6
					xpos = visibleWidth - 16
					# shiftx = shiftx * len(str(self.keyGlyphMargin))
					shiftx, _y = textSize(str(self.keyGlyphMargin))
					fill(0)
					text(str(self.keyGlyphMargin), (xpos - shiftx, visibleHeight - 17))
					if self.diffMarginsInGroup:
						fillRGB(COLOR_KERN_VALUE_NEGATIVE)
						oval(visibleWidth - 13, visibleHeight - 14, 8, 8)

				elif self.direction == 'R':
					if self.showMask:
						fill(.4)
						if self.font.info.italicAngle != 0:
							a = self.font.info.italicAngle
							h = visibleHeight
							w = visibleWidth
							polygon((w / 2 - italicShift(a, h) / 2, 0), (w / 2 + italicShift(a, h) / 2, h), (w, h),
							        (w, 0))
						else:
							rect((visibleWidth / 2), 0, visibleWidth / 2, visibleHeight)
					fill(0)
					text(str(self.keyGlyphMargin), (17, visibleHeight - 17))
					if self.diffMarginsInGroup:
						fillRGB(COLOR_KERN_VALUE_NEGATIVE)
						oval(5, visibleHeight - 14, 8, 8)

				# font('Menlo', fontSize = 10)
				fill(0)
				if self.showSelected:
					fill(.1, 0, 1, 1)
				# fill()
				# print NSColor.selectedMenuItemTextColor()
				rect(0, 0, visibleWidth, 15)
				txt = getDisplayNameGroup(self.groupname)
				txtshift = 2
				font('.SFCompactText-Regular', fontSize = 10)
				if txt.startswith('@.'):
					txt = txt.replace('@.','')
					txtshift = 10
					fillRGB((1,.6,.2,1))
					text('@', 3,2)
				fill(1)
				nx,ny = textSize(txt)
				if nx > visibleWidth-15:
					font('.SFCompactText-Regular', fontSize = 8)
					text(txt, (3 + txtshift, 3))
				else:
					text(txt, (3 + txtshift, 1))
				translate(visibleWidth / 2 - visibleWidth / 40, (visibleHeight / 3))  # -4

				stroke(0, 0, 0, 0)
				strokeWidth(0)
				scale(scalefactor)

				for idx, glyph in enumerate(self.glyphsToDisplay):
					save()
					pen = CocoaPen(self.font)
					if self.direction == 'L':
						translate(Xright - glyph.width, self.vertShift)
					elif self.direction == 'R':
						translate(Xleft, self.vertShift)
					fill(0, 0, 0, self._alpha)
					if glyph.name == self.keyGlyph:
						fill(0, 0, 0, 1)
					glyph.draw(pen)
					drawPath(pen.path)

					restore()
					translate(0, 0)


class TDGroupLine(VanillaBaseObject):
	nsViewClass = NSView

	def __init__ (self, posSize, separatePairs=True,
	              selectionCallback=None,
	              selectionPairCallback = None,
	              selectionGlyphCallback = None,
	              sizeStyle='regular',
	              hasHorizontalScroller=True, showValues=False, showMargins = False, showNames = False):
		xw, yw, tx, ty = posSize
		# ty = 120
		# self._posSize = (xw, yw, tx, 106)
		self.glyphsToDisplay = []
		self.pairsToDisplay = None
		self.pairsViews = []
		self._currentPairToDisplay = ()
		self._font = None
		self._viewArray = []
		self._selectedGlyph = None
		self._idxSelectedGlyph = 0
		self._letterStep = 7
		self._hasHorizontalScroller = hasHorizontalScroller
		self.hashKernDic = None
		self.separatorPairsWidth = 250
		self.separatePairs = separatePairs
		self.toucheMode = False
		self.touchFlag = False
		self.lightmode = False
		self.valuesMode = showValues
		self.showMargins = showMargins
		self.showNames = showNames
		self.maxX = 0
		self._mouseOver = False

		self.darkmode = KERNTOOL_UI_DARKMODE
		self.darkmodeWarm = KERNTOOL_UI_DARKMODE_WARMBACKGROUND

		self._scalefactorUI = .045  # sizeStyle = 'regular'
		ty = 85

		if sizeStyle == 'extrabig':
			self._scalefactorUI = .090
			ty = 180
		if sizeStyle == 'big':
			self._scalefactorUI = .055
			ty = 110
		elif sizeStyle == 'small':
			self._scalefactorUI = .035
			ty = 65
			self.valuesMode = False
			self.showMargins = False
			self.showNames = False
		elif sizeStyle == 'mini':
			self._scalefactorUI = .027
			ty = 50
			self.valuesMode = False
			self.showMargins = False
			self.showNames = False
		elif sizeStyle == 'micro':
			self._scalefactorUI = .021
			ty = 40
			self.valuesMode = False
			self.showMargins = False
			self.showNames = False
		self.heightOfControl = ty

		self._selectedPair = None
		self._selectionCallback = selectionCallback
		self._selectionPairCallback = selectionPairCallback
		self._selectionGlyphCallback = selectionGlyphCallback
		self._selfHeight = ty
		self._setupView(self.nsViewClass, (xw, yw, tx, ty))  # (0, 0, -0, 106)
		self.infoLine = Canvas((0, 0, -0, -0),
		                       delegate = self,  # canvasSize = (100, 101),
		                       hasHorizontalScroller = hasHorizontalScroller,
		                       hasVerticalScroller = False,
		                       autohidesScrollers = True,
		                       # backgroundColor = NSColor.whiteColor()
		                       )
		self.infoLine.scrollView.getNSScrollView().setBorderType_(NSNoBorder)
		# self.infoLine.update()

	def setFont (self, font, hashKernDic):
		self._font = font
		self.hashKernDic = hashKernDic
		self.setPairsToDisplay([],[])
		# self.glyphsToDisplay = []
		# self.pairsToDisplay = None
		# self.pairsViews = []
		# # self._currentPairToDisplay = ()
		# # self._viewArray = []
		# # self._selectedGlyph = None
		# # self._idxSelectedGlyph = 0
		# self.compilePairs()
		# # self.infoLine.update()



	def setPairsToDisplay (self, glyphsListUUID, pairList):
		# print 'got list:'
		if self.glyphsToDisplay != glyphsListUUID:
			self.resetPosition()
		self.glyphsToDisplay = glyphsListUUID
		self.pairsToDisplay = pairList
		self.compilePairs()
		self.infoLine.update()

	def setPair (self, pair, direction = None, deltaKern = None):
		if not direction: return
		l, r = pair
		pair = researchPair(self._font, self.hashKernDic, (l, r))

		gL = pair['L_nameForKern']
		gR = pair['R_nameForKern']
		ggL = []
		ggR = []
		if direction == 'L':
			if self.hashKernDic.thisGroupIsMMK(gL):
				try:
					for ggname in self._font.groups[gL]:
						ggL.append(self._font[ggname].name)
						ggL.append(self._font[cutUniqName(r)].name)
				except: pass
			self.setPairsToDisplay(ggL, getListOfPairsToDisplay(self._font, self.hashKernDic, ggL, deltaKern = deltaKern))

		elif direction == 'R':
			if self.hashKernDic.thisGroupIsMMK(gR):
				try:
					for ggname in self._font.groups[gR]:
						ggR.append(self._font[cutUniqName(l)].name)
						ggR.append(self._font[ggname].name)
				except: pass
			self.setPairsToDisplay(ggR, getListOfPairsToDisplay(self._font, self.hashKernDic, ggR, deltaKern = deltaKern))
		elif direction == 'B':
			self.setPairsToDisplay([l, r], getListOfPairsToDisplay_previewDeltaKern(self._font, self.hashKernDic, [l, r], deltaKern = deltaKern, mixPairs = False))
			return

		if not self.hashKernDic.thisGroupIsMMK(gL) and not self.hashKernDic.thisGroupIsMMK(gR):
			self.setPairsToDisplay([gL, gR], getListOfPairsToDisplay(self._font, self.hashKernDic, [gL, gR],deltaKern = deltaKern))

	def setGlyphsLine(self, glyphslist):
		if glyphslist:
			self.setPairsToDisplay(glyphslist, getListOfPairsToDisplay(self._font, self.hashKernDic, glyphslist))


	def get (self):
		return self.glyphsToDisplay

	def mouseDown (self, event):

		offset = self.separatorPairsWidth * self._scalefactorUI
		X_window_pos = event.locationInWindow().x
		X_local_pos = self.infoLine.scrollView.getNSScrollView().documentVisibleRect().origin.x
		x = X_window_pos + X_local_pos # - self._letterStep
		selectedpair = ()
		item = None
		for idx, item in enumerate(self._viewArray):
			# if idx+1 < len(self._viewArray):
			x0 = item['x0'] + offset
			# x1 = self._viewArray[idx+1]['x1']
			x1 = item['x0'] + item['width']* self._scalefactorUI - item['kernValue']* self._scalefactorUI + offset #+ self._viewArray[idx+1]['width']* self._scalefactorUI + offset
			if ( x0 < x ) and ( x < x1 ) :
				self._selectedGlyph = item
				self._idxSelectedGlyph = idx
				# print ('item', item)
				# print ('idx',idx)
				for pitem in self.pairsViews:

					pl , pr = pitem
					if pl == self._viewArray[idx - 1]['nameUUID'] and pr == item['nameUUID'] :
						selectedpair = (cutUniqName(self._viewArray[idx - 1]['nameUUID']), cutUniqName(item['nameUUID']))
						# self._idxSelectedGlyph = idx
					if pl == item['nameUUID'] and pr == self._viewArray[idx + 1]['nameUUID']:
						selectedpair = (cutUniqName(item['nameUUID']), cutUniqName(self._viewArray[idx + 1]['nameUUID']))
						# self._idxSelectedGlyph = idx + 1

				break
		if event.clickCount() == 2:
			if self._selectionCallback:
				self._selectionCallback(self.glyphsToDisplay)
		else:
			if decodeModifiers(event.modifierFlags()) == 'Alt':
				if self._selectionPairCallback and selectedpair:
					self._selectionPairCallback(selectedpair)
			else:
				if self._selectionGlyphCallback and item:
					# print (self._idxSelectedGlyph)
					self._selectionGlyphCallback(cutUniqName(self._viewArray[self._idxSelectedGlyph]['nameUUID']))
		self.infoLine.update()




	def resetView (self):
		self._viewArray = []
		self.infoLine.update()

	def compilePairs (self):
		carretX = 0
		x_1 = 0
		self._viewArray = []
		self.pairsViews = []
		x_0 = 0
		pcount = 0
		lg = None
		rg = None
		for idx, glyphname in enumerate(self.glyphsToDisplay):
			# rulGlyph = []
			kernValue = 0
			if self.pairsToDisplay and (idx < len(self.pairsToDisplay)):
				pair = self.pairsToDisplay[idx]
				kernValue = pair['kernValue']
			realname = cutUniqName(glyphname)
			glyph = self._font[realname]

			inGroup = False
			nameToDisplay = realname
			nameUUID = glyphname + '.' + getUniqName()

			if not kern(kernValue):
				kernValue = 0
			carret = (kernValue + glyph.width)  # * .2
			x_1 = x_0 + carret
			self._viewArray.append({'x0': x_0 * self._scalefactorUI, 'x1': x_1 * self._scalefactorUI,
			                        'name': nameToDisplay,  # 'name': cutUniqName(glyphname),
			                        'nameUUID': nameUUID,
			                        'width': glyph.width,
			                        'kernValue': kernValue,  # 'leftMargin': s_Lm,  # 'rightMargin': s_Rm,
			                        'inGroup': inGroup})
			x_0 = x_1

			if self.separatePairs:
				pcount += 1
				if pcount == 2:
					x_0 += self.separatorPairsWidth
					pcount = 0
					self.pairsViews.append((self._viewArray[idx-1]['nameUUID'],nameUUID))

	def resetPosition (self):
		point = NSPoint(0, 0)
		self.infoLine.scrollView.getNSScrollView().contentView().scrollToPoint_(point)
		self.infoLine.scrollView.getNSScrollView().reflectScrolledClipView_(
			self.infoLine.scrollView.getNSScrollView().contentView())

	def scrollWheel (self, event):
		if not self._hasHorizontalScroller: return
		deltaX = event.deltaX()
		deltaY = 0
		if deltaY == 0 and deltaX == 0 : return

		scaleScroll = 5
		visibleWidth = self.infoLine.scrollView.getNSScrollView().documentVisibleRect().size.width -20
		visibleHeight = self.infoLine.scrollView.getNSScrollView().documentVisibleRect().size.height
		posXscroller = self.infoLine.scrollView.getNSScrollView().documentVisibleRect().origin.x
		posYscroller = self.infoLine.scrollView.getNSScrollView().documentVisibleRect().origin.y

		xW, yW, wW, hW = self.getPosSize()
		xpoint = posXscroller - (deltaX * scaleScroll)
		if xpoint < xW :
			xpoint = 0
		if xpoint > self.maxX - visibleWidth:
			xpoint = self.maxX - visibleWidth #+ 200
		point = NSPoint(xpoint, posYscroller + (deltaY * scaleScroll))
		self.infoLine.scrollView.getNSScrollView().contentView().scrollToPoint_(point)
		self.infoLine.scrollView.getNSScrollView().reflectScrolledClipView_(
			self.infoLine.scrollView.getNSScrollView().contentView())

	def draw (self):
		self._viewFontName = 'Menlo'
		stroke(0, 0, 0, 0)
		strokeWidth(0)


		def drawSelectionCursor (x, y, color, markException=False):
			opt = 0
			if markException:
				opt = 20
			hw = 70 + opt
			x = x - hw
			fillRGB(color)
			newPath()
			moveTo((x, y))
			lineTo((x + hw, y + hw + hw/3 - opt))
			lineTo((x + hw * 2, y))
			closePath()
			drawPath()
			if markException:

				fill(1)
				if self.darkmodeWarm:
					fillRGB((.75, .73, .7, 1))
				oh = 80
				oval(x+(hw*2-oh)/2, y-oh/2 + 10, oh, oh)
				fillRGB(COLOR_KERN_VALUE_NEGATIVE)
				oh = 55
				oval(x + (hw * 2 - oh) / 2, y - oh / 2 +10, oh, oh)

		# self._viewFontSize = 6 #* self._scalefactorUI
		# font(self._viewFontName, fontSize = self._viewFontSize)
		visibleHeight = self.infoLine.scrollView.getNSScrollView().documentVisibleRect().size.height
		ruller_compensation = self._selfHeight - visibleHeight

		X_local_pos = self.infoLine.scrollView.getNSScrollView().documentVisibleRect().origin.x
		visibleHeight = self.infoLine.scrollView.getNSScrollView().documentVisibleRect().size.height

		Y_local_pos = self.infoLine.scrollView.getNSScrollView().documentVisibleRect().origin.y
		visibleWidth = self.infoLine.scrollView.getNSScrollView().documentVisibleRect().size.width

		Ypos = 0  # visibleHeight - 20
		Ybase = Ypos

		maxX = 0
		Xpos = 0
		scalefactor = self._scalefactorUI
		shiftX = 200
		maxX += shiftX

		# self.darkmode = True
		if self.darkmodeWarm:
			fillRGB((.75, .73, .7, .8))
			_rw = self.maxX+100
			# print('maxY', maxY)
			if _rw < visibleWidth:
				_rw = visibleWidth #+ 500
			rect(0, 0, _rw, visibleHeight)



		fillRGB(COLOR_BLACK)



		translate(shiftX * scalefactor, (visibleHeight / 3))  # * 2 )
		save()
		stroke(0, 0, 0, 0)
		strokeWidth(0)
		scale(scalefactor)
		pcount = 0

		# showSeparator = True
		widthSeparator = self.separatorPairsWidth
		paircount = len(self._viewArray)
		for idx, item in enumerate(self._viewArray):
			fillRGB(COLOR_BLACK)

			if self.toucheMode and not self.lightmode:
				if self.touchFlag:
					fillRGB(COLOR_TOUCHE)
					self.touchFlag = False
				if idx + 1 < len(self._viewArray):
					# if item['y0'] == self._viewArray[idx + 1]['y0']:
					kernValue = item['kernValue']
					if kernValue == None: kernValue = 0
					currGlyph = self._font[item['name']]
					nextGlyph = self._font[self._viewArray[idx + 1]['name']]
					if checkOverlapingGlyphs(currGlyph, nextGlyph, kernValue):
						fillRGB(COLOR_TOUCHE)
						self.touchFlag = True
			save()
			# try:
			maxX = item['x1']
			glyph = self._font[item['name']]
			Xpos = item['x0'] / scalefactor
			pen = CocoaPen(self._font)
			translate(Xpos, 0)
			glyph.draw(pen)
			drawPath(pen.path)
			# except:
			# 	pass
			# translate(0,0)
			# Xpos = item['kernValue'] + item['width']

			if self.showMargins:
				translate(-Xpos, 0)
				self._viewFontSize = 80
				font(self._viewFontName, fontSize = self._viewFontSize)
				HVcontrol = 60
				Vcontrol = 80
				HVkern = 60
				Ycontrol = -400
				xlM = Xpos# item['x0']
				xrM = Xpos + item['width']+scalefactor
				t1 = Ycontrol + 120  # + 1200
				t2 = HVcontrol
				wbar = 150
				lbar = 5
				gapbar = 30
				glyph = self._font[item['name']]
				if self._font.info.italicAngle == 0 or not self._font.info.italicAngle:
					lM = int(round(glyph.leftMargin, 0))
					rM = int(round(glyph.rightMargin, 0))
				else:
					lM = int(round(glyph.angledLeftMargin, 0))
					rM = int(round(glyph.angledRightMargin, 0))

				fill(.5)
				if self.darkmodeWarm:
					fill(.3, .3, .3, 1)
				# leftMargin mark
				rect(xlM, t1, lbar, t2)  # vbar
				rect(xlM, t1 + t2 - lbar, wbar, lbar)  # hbar
				text(str(lM), (xlM + 30, t1 - 40))

				# rightMargin mark
				rect(xrM - wbar, t1 + t2 - lbar + gapbar, wbar, lbar)  # hbar
				rect(xrM - lbar, t1 + t2 - lbar + gapbar, lbar, t2 + lbar)  # vbar
				rm = str(rM)
				# rmoff = len(rm)*40 + 45
				nx, ny = textSize(rm)
				text(rm, (xrM - nx - 30, t1 + gapbar + 60))

				self.showSelected = True
				if self.showSelected and idx == self._idxSelectedGlyph:
					# fillRGB(COLOR_L_GROUP_ICON)
					drawSelectionCursor(xlM + item['width'] / 2, Ycontrol - 180, COLOR_L_GROUP_ICON) #+ item['width'] / 2 - lbar / 2 - wbar / 2
				else:
					rect(xlM + item['width'] / 2 - lbar / 2, Ycontrol - 180 + lbar, lbar, t2) # vbar
					# if (item['lineNumberOfPairs'] != self._selectedLine):
					rect(xlM + item['width'] / 2 - lbar / 2 - wbar / 2, Ycontrol - 180, wbar, lbar) # hbar
				if self.showNames:
					gn = item['name']
					nx, ny = textSize(gn)

					if nx > item['width']:
						l = len(gn) // 2
						a1 = ''.join(gn[:l]) + '-'
						nx, ny = textSize(a1)
						b1 = ''.join(gn[l:])
						text(a1, (xlM + item['width'] / 2 - nx / 2, Ycontrol + 1600))
						text(b1, (xlM + item['width'] / 2 - nx / 2, Ycontrol + 1520))
					else:
						text(gn,(xlM + item['width'] / 2 - nx / 2, Ycontrol + 1520 ))
					rect(xlM + item['width'] / 2 - lbar / 2, Ycontrol + 1500 - HVcontrol , lbar, t2)  # vbar
					# if (item['lineNumberOfPairs'] != self._selectedLine):
					rect(xlM + item['width'] / 2 - lbar / 2 - wbar / 2, Ycontrol + 1500, wbar, lbar)  # hbar



			restore()

		restore()
		pcount = 0
		self._viewFontSize = 80 * scalefactor
		font(self._viewFontName, fontSize = self._viewFontSize)

		translate(0, -1 * (visibleHeight / 9) * 2)
		if self.pairsToDisplay:
			# print self._pairsToDisplay
			for idx, pair in enumerate(self.pairsToDisplay):
				if idx < len(self._viewArray):
					item = self._viewArray[idx]
					x1L = item['x1']

					HVcontrol = 60 * scalefactor
					Vcontrol = 80
					HVkern = 60 * scalefactor
					Ycontrol = 0

					if item['kernValue'] != None and not pair['exception'] and pcount != 1:
						kV = item['kernValue']
						if kV in range(1, 60):
							kV = 60
						if kV in range(-60, 0):
							kV = -60
						xK = item['x0'] + item['width'] * scalefactor
						if kV > 0:
							xK = item['x0'] + item['width'] * scalefactor  # + (shiftX * scalefactor)
							fillRGB(COLOR_KERN_VALUE_POSITIVE)
							rect(xK, Ycontrol + HVcontrol, abs(kV) * scalefactor, HVkern)
							if self.valuesMode:
								text(str(item['kernValue']), (xK + abs(kV) * scalefactor + 3, Ycontrol - HVcontrol))
						# if item['exception']:
						# 	drawException(xK + abs(kV) / 2 - HVcontrol, Ycontrol - HVcontrol)
						# rect(xK, Ycontrol + HVcontrol, HVkern, HVkern)
						elif kV < 0:
							# xK = item['width']
							xK = item['x1']  # - HVkern/2# * scalefactor# + (shiftX * scalefactor)
							fillRGB(COLOR_KERN_VALUE_NEGATIVE)
							rect(xK, Ycontrol + HVcontrol, abs(kV) * scalefactor, HVkern)
							if self.valuesMode:
								text(str(item['kernValue']), (xK + abs(kV) * scalefactor + 3, Ycontrol - HVcontrol))

					if pair['exception'] and pcount != 1:
						kV = item['kernValue']
						if kV > 0:
							xK = item['x0'] + (item['width'] * scalefactor) - 4  # + (shiftX * scalefactor)
							fillRGB(COLOR_KERN_VALUE_POSITIVE)
							if self.valuesMode:
								text(str(kV), (xK + abs(kV) * scalefactor + 5, Ycontrol - HVcontrol))
						else:  # kV < 0:
							xK = item['x1'] - 4  # + (shiftX * scalefactor)
							fillRGB(COLOR_KERN_VALUE_NEGATIVE)
							if self.valuesMode:
								text(str(kV), (xK + abs(kV) * scalefactor + 5, Ycontrol - HVcontrol))
						x = xK
						y = 0
						s = 1.1
						newPath()
						moveTo((x + s * 4, y + s * 8))
						lineTo((x + s * 1, y + s * 3))
						lineTo((x + s * 4, y + s * 3))
						lineTo((x + s * 4, y + s * 0))
						lineTo((x + s * 7, y + s * 5))
						lineTo((x + s * 4, y + s * 5))
						closePath()
						drawPath()

				if self.separatePairs:
					pcount += 1
					if pcount == 2:
						# translate(widthSeparator * scalefactor, 0)
						pcount = 0
		# if self.separatePairs:
		# 	maxX += (widthSeparator*(paircount-2))* scalefactor

		if maxX < visibleWidth: maxX = visibleWidth
		self.infoLine._view.setFrame_(NSMakeRect(0, 0, maxX + 40, visibleHeight))
		self.maxX = maxX

class TDGroupViewLinesAndStackLR(VanillaBaseObject):
	nsViewClass = NSView

	def __init__ (self, parent, posSize, selectionCallback=None, selectionPairCallback = None,
	              showValues=False, stackedGroupDBLclickCallback = None):
		xw, yw, tx, ty = posSize
		self.font = None
		self.hashKernDic = None
		self.w = parent
		hGRPcontrols = 85
		sp = 1
		# self._selectionCallback = selectionCallback
		self._setupView(self.nsViewClass, (xw, yw, tx, hGRPcontrols * 2 +sp*4))
		# self.w = Group((0, 0, -0, -0))
		self.w.groupLineL = TDGroupLine(posSize = (xw, yw, -104, hGRPcontrols),
		                                selectionCallback = selectionCallback,
		                                selectionPairCallback = selectionPairCallback)
		self.w.groupLineR = TDGroupLine(posSize = (xw, yw + hGRPcontrols + sp, -104, hGRPcontrols),
		                                selectionCallback = selectionCallback,
		                                selectionPairCallback = selectionPairCallback)
		self.w.groupStackL = TDGroupViewStacked(posSize = (-103, yw, tx, hGRPcontrols),
		                                        doubleClickCallback = stackedGroupDBLclickCallback)
		self.w.groupStackR = TDGroupViewStacked(posSize = (-103, yw + hGRPcontrols + sp, tx, hGRPcontrols),
		                                        doubleClickCallback = stackedGroupDBLclickCallback)


	def setFont(self, font, hashKernDic):
		self.font = font
		self.hashKernDic = hashKernDic

		self.w.groupStackL.setFont(font)
		self.w.groupStackR.setFont(font)
		self.w.groupLineL.setFont(font, hashKernDic)
		self.w.groupLineR.setFont(font, hashKernDic)


	def getKeyGlyph (self, groupname, direction):
		if self.hashKernDic.thisGroupIsMMK(groupname):
			# totalglyphs = len(self.font.groups[groupname])
			if len(self.font.groups[groupname]) > 0:
				gname = self.font.groups[groupname][0]
				return (gname , getKeyGlyphMargin(self.font, keyglyph = gname, direction = direction))
		elif groupname in self.font:
				return (groupname, getKeyGlyphMargin(self.font, keyglyph = groupname, direction = direction))
		return (None, 0)

	def setPair(self, pair):
		l, r = pair
		l = cutUniqName(l)
		r = cutUniqName(r)
		pair = researchPair(self.font, self.hashKernDic, (l, r))
		gL = pair['L_nameForKern']
		gR = pair['R_nameForKern']
		ggL = []
		ggR = []
		gggL = []
		gggR = []


		diffMarginsInGroup = False
		if self.hashKernDic.thisGroupIsMMK(gL):
			(keyglyph, margin) = self.getKeyGlyph(gL, direction = 'L')
			for ggname in self.font.groups[gL]:
				if not diffMarginsInGroup and margin != getKeyGlyphMargin(self.font, keyglyph = ggname, direction = 'L'):
					diffMarginsInGroup = True
				ggL.append( ggname )
				gggL.append(self.font[ggname])
				ggL.append( r )
		else:
			(keyglyph, margin) = self.getKeyGlyph(l, direction = 'L')
			ggL.append(l)
			gggL.append(self.font[l])
			ggL.append(r)
		self.w.groupLineL.setPairsToDisplay(ggL, getListOfPairsToDisplay(self.font, self.hashKernDic, ggL))
		self.w.groupStackL.setupGroupViewExternal(gL, gggL, keyglyph, margin, diffMarginsInGroup, 'L' )


		diffMarginsInGroup = False
		if self.hashKernDic.thisGroupIsMMK(gR):
			totalglyphs = len(self.font.groups[gR])

			(keyglyph, margin) = self.getKeyGlyph(gR, direction = 'R')
			for ggname in self.font.groups[gR]:
				if margin != getKeyGlyphMargin(self.font, keyglyph = ggname, direction = 'R'):
					diffMarginsInGroup = True
				ggR.append( l )
				ggR.append( ggname )
				gggR.append(self.font[ggname])
		else:
			(keyglyph, margin) = self.getKeyGlyph(r, direction = 'R')
			ggR.append(l)
			gggR.append(self.font[r])
			ggR.append(r)
		self.w.groupLineR.setPairsToDisplay(ggR, getListOfPairsToDisplay(self.font, self.hashKernDic, ggR))
		self.w.groupStackR.setupGroupViewExternal(gR, gggR, keyglyph, margin, diffMarginsInGroup, 'R')

		# if not self.hashKernDic.thisGroupIsMMK(gL) and not self.hashKernDic.thisGroupIsMMK(gR):
		# 	self.groupLineL.setPairsToDisplay([gL], getListOfPairsToDisplay(self.font, self.hashKernDic, [gL, gR]))




# TEST Section
if __name__ == "__main__":
	class MyW(object):
		def __init__ (self):
			self.w = Window((500, 400), "InfoLine", minSize = (200, 100))
			hGRPcontrols = 85
			yInfoControl = 20

			self.font = CurrentFont()
			nextG = 5
			self.w.gC1 = TDGroupLine((5,nextG,-5,0),
			                        separatePairs=False,
			                        selectionCallback=None,
			                        selectionPairCallback = None,
	                                sizeStyle='extrabig',
	                                hasHorizontalScroller=True,
	                                showValues=True,
	                                showMargins = True,
			                        showNames = True
			                        )
			nextG += self.w.gC1.heightOfControl+2

			self.w.gC2 = TDGroupLine((5, nextG, -5, 0),
			                        separatePairs = False,
			                        selectionCallback = None,
			                        selectionPairCallback = None,
			                        sizeStyle = 'big',
			                        hasHorizontalScroller = True,
			                        showValues = True,
			                        showMargins = True,
			                        showNames = True
			                        )
			nextG += self.w.gC2.heightOfControl+2

			self.w.gC3 = TDGroupLine((5, nextG, -5, 0),
			                        separatePairs = False,
			                        selectionCallback = None,
			                        selectionPairCallback = None,
			                        sizeStyle = 'regular',
			                        hasHorizontalScroller = True,
			                        showValues = True,
			                        showMargins = True,
			                        showNames = True
			                        )
			nextG += self.w.gC3.heightOfControl+2

			self.w.gC4 = TDGroupLine((5, nextG, -5, 0),
			                        separatePairs = False,
			                        selectionCallback = None,
			                        selectionPairCallback = None,
			                        sizeStyle = 'small',
			                        hasHorizontalScroller = True,
			                        showValues = True,
			                        showMargins = True,
			                        showNames = True
			                        )
			nextG += self.w.gC4.heightOfControl+2

			self.w.gC5 = TDGroupLine((5, nextG, -5, 0),
			                        separatePairs = False,
			                        selectionCallback = None,
			                        selectionPairCallback = None,
			                        sizeStyle = 'mini',
			                        hasHorizontalScroller = True,
			                        showValues = True,
			                        showMargins = True,
			                        showNames = True
			                        )
			nextG += self.w.gC5.heightOfControl+2

			self.w.gC6 = TDGroupLine((5, nextG, -5, 0),
			                        separatePairs = False,
			                        selectionCallback = None,
			                        selectionPairCallback = None,
			                        sizeStyle = 'micro',
			                        hasHorizontalScroller = True,
			                        showValues = True,
			                        showMargins = True,
			                        showNames = True
			                        )
			nextG += self.w.gC6.heightOfControl



			self.hashKernDic = TDHashKernDic(self.font)
			l = 'A'
			r = 'O'
			self.w.open()

			self.w.gC1.setFont(self.font, self.hashKernDic)
			self.w.gC1.setPair((l,r),direction = 'R')
			self.w.gC2.setFont(self.font, self.hashKernDic)
			self.w.gC2.setPair((l, r), direction = 'R')
			self.w.gC3.setFont(self.font, self.hashKernDic)
			self.w.gC3.setPair((l, r), direction = 'R')
			self.w.gC4.setFont(self.font, self.hashKernDic)
			self.w.gC4.setPair((l, r), direction = 'R')
			self.w.gC5.setFont(self.font, self.hashKernDic)
			self.w.gC5.setPair((l, r), direction = 'R')
			self.w.gC6.setFont(self.font, self.hashKernDic)
			self.w.gC6.setPair((l, r), direction = 'R')



	MyW()
