# -*- coding: utf-8 -*-

from vanilla import *
# from AppKit import *
import AppKit
from fontTools.pens.cocoaPen import CocoaPen
from mojo.canvas import Canvas
from mojo.drawingTools import *
from fontParts.world import CurrentFont
from lib.eventTools.eventManager import postEvent, publishEvent
from mojo.events import addObserver, removeObserver
from vanilla.dialogs import getFile
import codecs, sys, os
import uuid
from defconAppKit.controls.glyphCollectionView import GlyphCollectionView
import time

import importlib
import tdCanvasKeysDecoder

importlib.reload(tdCanvasKeysDecoder)
from tdCanvasKeysDecoder import decodeCanvasKeys, decodeModifiers

import tdKernToolEssentials

importlib.reload(tdKernToolEssentials)
from tdKernToolEssentials import *

# import touche

# reload(touche)
# from touche import *

# sys.path.append('/Users/alexander/PycharmProjects/Anchorman')
import tdGlyphparser

importlib.reload(tdGlyphparser)


class TDMenuAdvanced(VanillaBaseObject):
	nsViewClass = AppKit.NSView

	def __init__ (self, posSize, selectionCallback=None, window=None):
		xw, yw, tx, ty = posSize
		self._window = window
		self._linesToDisplay = []
		# self._font = None
		self._fontMenu = []
		self._viewArray = []
		self._selectedLine = 0
		self._positionYselected = 0
		self._lineSize = 1800  # 1800 # 1800=1000upm; 2400=2000upm
		self.Ygap = 0  # - yw*2
		self.shiftX = 150
		self._scalefactorUI = .03
		self.scaleStep = 1.2
		self.lineCount = 0
		self.maxX = 0
		self.maxXX = 0


		self._lastGlyphXpos = 0

		self._selectionCallback = selectionCallback
		self.showselection = False
		self._setupView(self.nsViewClass, (xw, yw, tx, ty))  # (0, 0, -0, 106)

		self.canvas = Canvas((0, 0, -0, -0),
		                     delegate = self,  # canvasSize = (100, 101),
		                     hasHorizontalScroller = False,
		                     hasVerticalScroller = True,
		                     autohidesScrollers = False,
		                     backgroundColor = AppKit.NSColor.whiteColor(),
		                     drawsBackground = True,
		                     # acceptsMouseMoved = True
		                     )
		self.canvas.scrollView.getNSScrollView().setBorderType_(AppKit.NSNoBorder)

		fonts = AllFonts()
		for font in fonts:
			if font.info.familyName and font.info.styleName:
			# print font.info.familyName
			# print font.info.styleName
				self.addMenuItem(font = font, title = font.info.familyName + ' ' + font.info.styleName)
		self.compileLines()
		# print self.w.menu._viewArray
		self.canvas.update()
		self.scrollToLine(0)

		# self.canvas.update()

	def addMenuItem (self, font, title):
		tline = []
		for glyphName in tdGlyphparser.translateText(font, title):
			tline.append('%s.%s' % (glyphName, getUniqName()))
		if tline:
			self._linesToDisplay.append({'font': font,
			                             'title': tline})

	def menuSelectedCallback (self):
		if self._selectionCallback:
			self._selectionCallback(self._linesToDisplay[self._selectedLine]['font'])
		self._window.close()

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

		point = AppKit.NSPoint(xpos, ypos)
		self.canvas.scrollView.getNSScrollView().contentView().scrollToPoint_(point)
		self.canvas.scrollView.getNSScrollView().reflectScrolledClipView_(
			self.canvas.scrollView.getNSScrollView().contentView())
		return firstItemInLine
		# if not self._viewArray: return
		# visibleWidth = self.canvas.scrollView.getNSScrollView().documentVisibleRect().size.width
		# visibleHeight = self.canvas.scrollView.getNSScrollView().documentVisibleRect().size.height
		# posXscroller = self.canvas.scrollView.getNSScrollView().documentVisibleRect().origin.x
		# posYscroller = self.canvas.scrollView.getNSScrollView().documentVisibleRect().origin.y
		# scale = self._scalefactorUI
		# xpos = 0
		# ypos = 0
		# for idx, item in enumerate(self._viewArray):
		# 	if item['lineNumberOfPairs'] == linenumber:
		# 		self._positionYselected = item['y0']
		# 		self._selectedLine = item['lineNumberOfPairs']
		# 		self._selectedBlock = item['blockNumberOfPairs']
		# 		break
		# # ypos = l['y0'] * scale
		# maxY = self._viewArray[-1]['y0']
		# y0 = (maxY + (-1 * self._positionYselected)) * scale
		# y1 = y0 + (self._lineSize * scale)
		#
		# if y0 < posYscroller:
		# 	ypos = y0
		# elif y1 - posYscroller > visibleHeight:
		# 	offset = visibleHeight - self._lineSize * scale
		# 	ypos = y0 - offset  # + posYscroller
		# else:
		# 	return
		#
		# point = NSPoint(xpos, ypos)
		# self.canvas.scrollView.getNSScrollView().contentView().scrollToPoint_(point)
		# self.canvas.scrollView.getNSScrollView().reflectScrolledClipView_(
		# 		self.canvas.scrollView.getNSScrollView().contentView())


	def scrollToBlock (self, linenumber):
		for item in self._viewArray:
			if item['blockNumberOfPairs'] == linenumber:
				# yPn = item['y0']
				self.scrollToLine(item['lineNumberOfPairs'])
				break

	def getSelectedLine (self):
		result = []
		for idx, item in enumerate(self._viewArray):
			if item['lineNumberOfPairs'] == self._selectedLine:
				result.append(item['name'])
		return '/' + '/'.join(result)

	def mouseDown (self, event):
		visibleHeight = self.canvas.scrollView.getNSScrollView().documentVisibleRect().size.height
		Y_local_pos = self.canvas.scrollView.getNSScrollView().documentVisibleRect().origin.y
		X_window_pos = event.locationInWindow().x
		Y_window_pos = event.locationInWindow().y
		X_local_pos = self.canvas.scrollView.getNSScrollView().documentVisibleRect().origin.x
		Y_local_pos = self.canvas.scrollView.getNSScrollView().documentVisibleRect().origin.y
		xW, yW, x2W, y2W = self.getPosSize()
		# print xW, yW, x2W, y2W
		x = X_window_pos + X_local_pos  # - self._letterStep
		y = Y_window_pos + y2W + Y_local_pos
		# print x, y

		self.showselection = True
		maxY = 0
		if self._viewArray:
			maxY = self._viewArray[-1]['y0']
		for idx, item in enumerate(self._viewArray):
			x0 = item['x0'] * self._scalefactorUI
			x1 = (item['x1'] + self.shiftX) * self._scalefactorUI
			# y0 = item['yV'] * self._scalefactorUI
			y0 = (maxY + (-1 * item['y0'])) * self._scalefactorUI
			# y1 = (y0 + self._lineSize) * self._scalefactorUI
			y1 = y0 + ((self._lineSize + self.Ygap) * self._scalefactorUI)  # - self.Ygap * self._scalefactorUI
			if (x0 < x and x < x1) and (y0 < y and y < y1):
				self._selectedLine = item['lineNumberOfPairs']
				self.canvas.update()
				self.menuSelectedCallback()
				# self._selectionCallback(self._selectedLine)
				# if event.clickCount() == 2:
				# 	if decodeModifiers(event.modifierFlags()) == 'Alt':
				# 		self.postMessageToKernTool(message = 'full line')
				# 	# postEvent('typedev.KernTool.setGlyphsLine', glyphsLine = self.getSelectedBlock())
				# 	else:
				# 		self.postMessageToKernTool(message = 'short line')
				# postEvent('typedev.KernTool.setGlyphsLine', glyphsLine = self.getSelectedLine())
				# print item['blockNumberOfPairs'], item['lineNumberOfPairs'] , x0, x1, y0, y1
				# self._packInfoForSelectionEvent()
				break

	def keyDown (self, event):
		# print event
		keypress = decodeCanvasKeys(event.keyCode(), event.modifierFlags())
		commands = translateKeyCodesToKernToolCommands(keypress)
		# if commands['command'] == COMMAND_ZOOM_IN:
		# 	scale = self._scalefactorUI * self.scaleStep
		# 	if scale < .3:
		# 		self._scalefactorUI = scale
		# 		self.setSize(self._scalefactorUI)
		#
		# if commands['command'] == COMMAND_ZOOM_OUT:
		# 	scale = self._scalefactorUI / self.scaleStep
		# 	if scale > .045:
		# 		self._scalefactorUI = scale
		# 		self.setSize(self._scalefactorUI)

		if commands['command'] == COMMAND_ENTER:
			# print 'need refresh'
			self.showselection = True
			# self._selectionCallback(self._selectedLine)
			self.menuSelectedCallback()
			self.canvas.update()
		# self.s
		if commands['command'] == COMMAND_ESCAPE:
			self._selectedLine = None
			self._window.close()
		# self.menuSelectedCallback()
		# print 'need refresh'
		# self.showselection = True
		# # self._selectionCallback(self._selectedLine)
		# self.menuSelectedCallback()
		# self.canvas.update()

		if commands['command'] == COMMAND_NEXT_LINE_SHORT:
			n = self._selectedLine + 1
			self.scrollToLine(n)
			self.canvas.update()
		if commands['command'] == COMMAND_PREV_LINE_SHORT:
			n = self._selectedLine - 1
			self.scrollToLine(n)
			self.canvas.update()
		# if commands['command'] == COMMAND_NEXT_LINE:
		# 	n = self._selectedBlock + 1
		# 	self.scrollToBlock(n)
		# 	self.canvas.update()
		# if commands['command'] == COMMAND_PREV_LINE:
		# 	n = self._selectedBlock - 1
		# 	self.scrollToBlock(n)
		# 	self.canvas.update()
		# if commands['command'] == COMMAND_SWITCH_TOUCHE_MODE:
		# 	self.toucheMode = not self.toucheMode
		# 	print 'touche mode:', self.toucheMode
		# 	self.canvas.update()
		# if commands['command'] == COMMAND_SWITCH_VALUES_MODE:
		# 	self.valuesMode = not self.valuesMode
		# 	print 'values mode:', self.valuesMode
		# 	self.canvas.update()
		# if commands['command'] == COMMAND_OPEN_PAIRS_FILE:
		# 	print 'open file'
		# 	pairsfile = getFile(messageText = 'message', title = 'title')
		# 	self.loadText(filepath = pairsfile)
		# 	self.canvas.update()
		# if commands['command'] == COMMAND_OPEN_PAIRS_BUILDER:
		# 	# print 'Pairs Builder'
		# 	self._pairsBuilder()

	def mouseUp (self, event):
		# pass
		self.showselection = False
		self.canvas.update()

	def compileLines (self, mode='rebuild'):  # mode = 'refresh'

		visibleWidth = 500  # self.visibleWidth

		self._viewArray = []
		self.maxX = 0
		# self.canvas.scrollView.getNSScrollView().documentVisibleRect().size.width
		scale = self._scalefactorUI

		lineStep = self._lineSize
		shiftX = self.shiftX
		Xshift = 50
		Xpos = shiftX
		Ypos = 0
		carret = 0
		smartmode = False
		self.lineCount = 0
		virtShift = 0
		widthvirt = 0
		kernValuevirt = 0
		idxLine = 0
		maxY = 0
		# if self._viewArray:
		# maxY = self._viewArray[-1]['y0']
		scalefactor = self._scalefactorUI
		# visibleWidth = self.visibleWidth
		# visibleHeight = self.canvas.scrollView.getNSScrollView().documentVisibleRect().size.height
		# ruller_compensation = self._selfHeight - visibleHeight

		# Y_local_pos = self.canvas.scrollView.getNSScrollView().documentVisibleRect().origin.y
		# X_local_pos = self.canvas.scrollView.getNSScrollView().documentVisibleRect().origin.x
		#
		# # print Y_local_pos
		# Y_min_window = Y_local_pos
		# Y_max_window = Y_local_pos + visibleHeight

		# if mode == 'rebuild':
		for menuitem in self._linesToDisplay:
			font = menuitem['font']
			title = menuitem['title']
			# line = item['line']
			# leftglyph = item['basic']
			# idxLine = item['idxLine']
			# YposV = item['Ypos']

			# self._viewArray = []
			# if not ((Y_min_window - self._lineSize * scalefactor <= ((maxY + (-1 * YposV)) * scalefactor)
			#     and Y_max_window >= ((maxY + (-1 * YposV)) * scalefactor))): break

			hashKernDic = TDHashKernDic(font = font)
			self._pairsToDisplay = getListOfPairsToDisplay(font, hashKernDic, title)

			for idx, glyphnameUUID in enumerate(title):
				kernValue = 0
				exception = False
				idxLine = idx
				if self._pairsToDisplay and (idx < len(self._pairsToDisplay)):
					pair = self._pairsToDisplay[idx]
					kernValue = pair['kernValue']
					exception = pair['exception']

				realname = cutUniqName(glyphnameUUID)
				glyph = font[realname]
				nameToDisplay = realname
				if not kernValue:
					kernValue = 0
				width = glyph.width
				self._viewArray.append({'name': cutUniqName(glyphnameUUID),
				                        'nameUUID': glyphnameUUID,
				                        'width': width,
				                        'font': font,
				                        'kernValue': pair['kernValue'],
				                        'exception': exception,
				                        'x0': Xpos,
				                        'x1': kernValue + Xpos + width,
				                        'y0': Ypos,
				                        'yV': Ypos,
				                        'blockNumberOfPairs': idxLine,
				                        'lineNumberOfPairs': self.lineCount,
				                        'virtual': False})
				Xpos += kernValue + width
				carret += kernValue + width
			carret = shiftX
			Ypos += lineStep
			Xpos = shiftX
			self.lineCount += 1
		# item['Ypos'] = Ypos
		self.recalculateFrame(visibleWidth)


	def scrollWheel(self, event):
		scaleUI = self._scalefactorUI
		# deltaX = event.deltaX()
		deltaY = event.deltaY()
		# print deltaY
		# if deltaY in range(0,1500): return# and deltaX == 0: return
		if deltaY == 0: return
		# if deltaY > 0 and
		# time.sleep(.02)
		scaleScroll = 2
		visibleWidth = self.canvas.scrollView.getNSScrollView().documentVisibleRect().size.width
		visibleHeight = self.canvas.scrollView.getNSScrollView().documentVisibleRect().size.height
		posXscroller = self.canvas.scrollView.getNSScrollView().documentVisibleRect().origin.x
		posYscroller = self.canvas.scrollView.getNSScrollView().documentVisibleRect().origin.y

		xW, yW, wW, hW = self.getPosSize()
		xpoint = 0
		# xpoint = posXscroller - (deltaX * scaleScroll)
		ypoint = posYscroller + (deltaY * scaleScroll)
		# if xpoint > self.maxXX - visibleWidth:  # - visibleWidth:
		# 	xpoint = self.maxXX - visibleWidth  # - self.visibleWidth #- visibleWidth
		# if xpoint < xW:
		# 	xpoint = 0
		# print deltaY, ypoint, posYscroller, visibleHeight
		if ypoint < 0:
			ypoint = 0
		# return
		maxY = 0
		if self._viewArray:
			maxY = self._viewArray[-1]['y0']
		if posYscroller + visibleHeight - self._lineSize * scaleUI > maxY * scaleUI:
			ypoint = maxY * scaleUI - visibleHeight + self._lineSize * scaleUI #- deltaY
			# ypoint = posYscroller + visibleHeight - self._lineSize * scaleUI
		elif posYscroller + visibleHeight - self._lineSize * scaleUI == maxY * scaleUI and deltaY>0:
			ypoint = maxY * scaleUI - visibleHeight + self._lineSize * scaleUI

		point = AppKit.NSPoint(xpoint, ypoint)
		self.canvas.scrollView.getNSScrollView().contentView().scrollToPoint_(point)
		self.canvas.scrollView.getNSScrollView().reflectScrolledClipView_(
			self.canvas.scrollView.getNSScrollView().contentView())
		# # if event.deltaY() > 0:
		# # 	self.stepToNextLine()
		# # elif event.deltaY() < 0:
		# # 	self.stepToPrevLine()
		# scaleUI = self._scalefactorUI
		# deltaX = event.deltaX()
		# deltaY = event.deltaY()
		# if deltaY == 0 and deltaX == 0 : return
		# # if deltaX > -10 and deltaX < 10  : deltaX = 0
		# # print deltaX
		# # print self.visibleWidth
		# scaleScroll = 5
		# visibleWidth = self.canvas.scrollView.getNSScrollView().documentVisibleRect().size.width
		# visibleHeight = self.canvas.scrollView.getNSScrollView().documentVisibleRect().size.height
		# posXscroller = self.canvas.scrollView.getNSScrollView().documentVisibleRect().origin.x
		# posYscroller = self.canvas.scrollView.getNSScrollView().documentVisibleRect().origin.y
		#
		# # print visibleWidth, self.visibleWidth
		#
		# # if posYscroller < 0 : posYscroller = 0
		# # if posXscroller < 0 : posXscroller = 0
		# # if visibleWidth > self.visibleWidth : deltaX = 0
		#
		# xW, yW, wW, hW = self.getPosSize()
		# xpoint = posXscroller - (deltaX * scaleScroll)
		# ypoint = posYscroller + (deltaY * scaleScroll)
		# if xpoint > self.maxXX - visibleWidth: #   - visibleWidth:
		# 	xpoint = self.maxXX - visibleWidth #- self.visibleWidth #- visibleWidth
		# if xpoint < xW:
		# 	xpoint = 0
		#
		# if ypoint < 0: ypoint = 0
		#
		# maxY = self._viewArray[-1]['y0']
		#
		# if posYscroller+visibleHeight-self._lineSize*scaleUI > maxY*scaleUI:
		#
		# 	ypoint = maxY*scaleUI - visibleHeight+self._lineSize*scaleUI
		#
		#
		#
		# point = NSPoint(xpoint, ypoint)
		#
		# self.canvas.scrollView.getNSScrollView().contentView().scrollToPoint_(point)
		# self.canvas.scrollView.getNSScrollView().reflectScrolledClipView_(
		# 	self.canvas.scrollView.getNSScrollView().contentView())
		# # self.canvas.update()


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
			yoff = visibleHeight  #+ 500
		self.canvas._view.setFrame_(AppKit.NSMakeRect(0, 0, visibleWidth + 60, yoff))
		self.maxXX = visibleWidth + 60
		# scalefactor = self._scalefactorUI
		#
		# if canvaswidth:
		# 	visibleWidth = canvaswidth
		# else:
		# 	visibleWidth = self.canvas.scrollView.getNSScrollView().documentVisibleRect().size.width
		# # print visibleWidth, self.maxX
		# # if self.maxX > visibleWidth:
		# # 	visibleWidth = self.maxX
		# self.visibleWidth = visibleWidth
		# visibleHeight = self.canvas.scrollView.getNSScrollView().documentVisibleRect().size.height
		# yoff = ((self.lineCount) * self._lineSize) * scalefactor
		# if yoff < visibleHeight:
		# 	yoff = visibleHeight
		# self.canvas._view.setFrame_(NSMakeRect(0, 0, visibleWidth, yoff))
		# self.maxXX = visibleWidth
		l, t, w, h = self._window.getPosSize()
		# # print l, t, w, h, ((self.lineCount+1) * self._lineSize) * scalefactor
		if self.lineCount < 5:
			self._window.resize(w, (((self.lineCount + 1) * self._lineSize) * scalefactor) -20)

	def draw (self):
		self.recalculateFrame(self.visibleWidth)
		self._viewFontName = 'Menlo'
		self._viewFontSize = 80
		font(self._viewFontName, fontSize = self._viewFontSize)
		visibleWidth = self.visibleWidth
		visibleHeight = self.canvas.scrollView.getNSScrollView().documentVisibleRect().size.height

		Y_local_pos = self.canvas.scrollView.getNSScrollView().documentVisibleRect().origin.y
		X_local_pos = self.canvas.scrollView.getNSScrollView().documentVisibleRect().origin.x

		scalefactor = self._scalefactorUI
		shiftX = self.shiftX
		Ygap = self.Ygap

		scale(scalefactor)
		stroke(0, 0, 0, 0)
		strokeWidth(0)
		Ygap =  250
		yoff = ((self.lineCount - 1) * self._lineSize) + Ygap
		# if (yoff * scalefactor) < visibleHeight:
		# 	yoff = (visibleHeight / scalefactor) - self._lineSize + Ygap
		# yoff = ((self.lineCount -1 ) * self._lineSize)# * scalefactor
		# if yoff < visibleHeight:
		# 	yoff = visibleHeight
		# 	yoff -= self._lineSize
		if self._viewArray:
			maxY = self._viewArray[-1]['y0']
		# y0 = (maxY + (-1 * r['y0'])) * scale
		# flag = False

		save()
		translate(shiftX, yoff + Ygap)
		for idx, item in enumerate(self._viewArray):
			# print item
			Xpos = item['x0']
			Ypos = item['y0']

			if (item['lineNumberOfPairs'] == self._selectedLine):
				if self.showselection:
					fillRGB(COLOR_L_PAIR_SELECTION)
				else:
					fillRGB(COLOR_R_PAIR_SELECTION)
				rect(-1 * shiftX, -1 * Ypos - 490, 500 / scalefactor, self._lineSize)

		restore()
		# save()
		translate(shiftX, yoff + Ygap)
		for idx, item in enumerate(self._viewArray):
			Xpos = item['x0']
			Ypos = item['y0']

			save()
			if (item['lineNumberOfPairs'] == self._selectedLine):
				fillRGB(COLOR_WHITE)
			else:
				fillRGB(COLOR_BLACK)
			glyph = item['font'][item['name']]
			pen = CocoaPen(item['font'])
			translate(Xpos, -1 * Ypos)
			# item['yV'] = yoff - Ypos  # - Ygap
			glyph.draw(pen)
			drawPath(pen.path)

			restore()


class MenuDialogWindow(object):
	def __init__ (self, parentWindow, callback=None):
		wW = 510
		hW = 300
		self.w = Sheet((wW, hW), parentWindow)
		self.callback = callback

		self.w.menu = TDMenuAdvanced((5, 5, -5, -30), window = self.w, selectionCallback = self.callback)

		self.w.btnApply = Button(((wW / 2) + 2, - 25, -10, 17), "Apply",
		                         callback = self.btnApplyCallback, sizeStyle = 'small')
		self.w.btnCancel = Button((10, - 25, (wW / 2) - 12, 17), "Cancel",
		                          callback = self.btnCloseCallback, sizeStyle = 'small')

		self.w.open()

	def get (self, sender):
		return self.w.menu._selectedLine

	def btnCloseCallback (self, sender):
		self.w.close()

	def btnApplyCallback (self, sender):
		self.w.menu.menuSelectedCallback()

	# self.w.close()


# TEST Section
if __name__ == "__main__":
	class MyW(object):
		def __init__ (self):
			self.w = Window((800, 300), "KMenu Tester", minSize = (200, 100))
			self.w.btn = Button((10, 10, 100, 20), "Menu",
			                    callback = self.btnOpenMenu, sizeStyle = 'small')

			self.w.open()

		# def getListOfOpenFonts (self):
		# 	listfonts = AllFonts()
		# 	lfonts = []
		# 	for n in listfonts:
		# 		fontFamilyName = '<empty font info>'
		# 		fontStyleName = '<empty font info>'
		# 		if n.info.familyName != None:
		# 			fontFamilyName = n.info.familyName
		# 		if n.info.styleName != None:
		# 			fontStyleName = n.info.styleName
		# 		lfonts.append(fontFamilyName + '/' + fontStyleName)
		# 	lfonts.sort()
		# 	return lfonts




		def selectFontCallback (self, info):
			print (info)

		def btnOpenMenu (self, sender):
			MenuDialogWindow(parentWindow = self.w, callback = self.selectFontCallback)

		def refresh (self):
			pass


	MyW()
