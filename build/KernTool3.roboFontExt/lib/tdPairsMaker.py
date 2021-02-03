# -*- coding: utf-8 -*-

from vanilla import *
from AppKit import *
from fontTools.pens.cocoaPen import CocoaPen
from mojo.canvas import Canvas
from mojo.drawingTools import *
from fontParts.world import CurrentFont
from lib.eventTools.eventManager import postEvent, publishEvent
from mojo.events import addObserver, removeObserver
from vanilla.dialogs import getFile, putFile
import codecs, sys, os
# import uuid
from defconAppKit.controls.glyphCollectionView import GlyphCollectionView

# from defconAppKit.controls.glyphCollectionView import GlyphCollectionView

import importlib
import tdCanvasKeysDecoder

importlib.reload(tdCanvasKeysDecoder)
from tdCanvasKeysDecoder import decodeCanvasKeys, decodeModifiers

import tdKernToolEssentials

importlib.reload(tdKernToolEssentials)
from tdKernToolEssentials import *

import tdMenuAdvanced

importlib.reload(tdMenuAdvanced)
from tdMenuAdvanced import MenuDialogWindow



# sys.path.append('/Users/alexander/PycharmProjects/Anchorman')
import tdGlyphparser
importlib.reload(tdGlyphparser)


class PairsBuilderDialogWindow(object):
	# nsViewClass = NSView

	def __init__ (self, parentWindow, font=None, kernhash = None,
	              callback=None,
	              leftList = [],
	              rightList = [],
	              patternLeft = [],
	              patternRight = []):
		wW = 650
		hW = 580
		self.w = Sheet((wW, hW), parentWindow, minSize = (wW,hW), maxSize = (wW,1000))

		self.callback = callback
		self.font = font
		self.leftList = leftList
		self.rightList = rightList
		self.patternLeft = patternLeft
		self.patternRight = patternRight
		self.pairsPerLine = None
		pLefttext = ''
		pRighttext = ''
		if patternLeft:
			pLefttext = '/'+'/'.join(patternLeft)
		if patternRight:
			pRighttext = '/'+'/'.join(patternRight)
		self.hashKernDic = kernhash
		# self._setupView(self.nsViewClass, (0, 0, wW, hW))
		dropSettings = dict(callback = self.groupsDropCallback)
		# GlyphCollectionView
		glyphCollectionShiftY = 760
		self.w.leftGlyphList = GlyphCollectionView((10, 32, (wW / 2) - 12, hW - glyphCollectionShiftY),
		                                           showModePlacard = False,
		                                           cellRepresentationName = "doodle.GlyphCell",
		                                           # initialMode = "cell",
		                                           listColumnDescriptions = None,
		                                           listShowColumnTitles = False,
		                                           showPlacard = False,
		                                           placardActionItems = None,
		                                           allowDrag = True,
		                                           selfWindowDropSettings = dropSettings,
		                                           selfApplicationDropSettings = dropSettings,
		                                           selfDropSettings = dropSettings,
		                                           otherApplicationDropSettings = dropSettings,
		                                           enableDelete = True
		                                           )
		# self.groupView.id = groupName
		self.w.leftGlyphList.id = 'leftgroup'
		self.w.leftGlyphList.setCellRepresentationArguments(drawHeader = True)  # , drawMetrics = True
		# self.setContent(content)
		# self.w.leftGlyphList.getNSScrollView().setHasVerticalScroller_(True)
		# self.w.leftGlyphList.getNSScrollView().setAutohidesScrollers_(False)
		# # self.w.leftGlyphList.getNSScrollView().setBackgroundColor_(NSColor.whiteColor())
		# self.w.leftGlyphList.getNSScrollView().setBorderType_(NSNoBorder)
		# GlyphCollectionView
		self.w.rightGlyphList = GlyphCollectionView(((wW / 2) + 2, 32, -10, hW - glyphCollectionShiftY),
		                                            showModePlacard = False,
		                                            cellRepresentationName = "doodle.GlyphCell",
		                                            # initialMode = "cell",
		                                            listColumnDescriptions = None,
		                                            listShowColumnTitles = False,
		                                            showPlacard = False,
		                                            placardActionItems = None,
		                                            allowDrag = True,
		                                            selfWindowDropSettings = dropSettings,
		                                            selfApplicationDropSettings = dropSettings,
		                                            selfDropSettings = dropSettings,
		                                            otherApplicationDropSettings = dropSettings,
		                                            enableDelete = True
		                                            )
		# self.groupView.id = groupName
		self.w.rightGlyphList.id = 'rightgroup'
		self.w.rightGlyphList.setCellRepresentationArguments(drawHeader = True)  # , drawMetrics = True
		# self.setContent(content)
		# self.w.rightGlyphList.getNSScrollView().setHasVerticalScroller_(True)
		# self.w.rightGlyphList.getNSScrollView().setAutohidesScrollers_(False)
		# # self.w.rightGlyphList.getNSScrollView().setBackgroundColor_(NSColor.whiteColor())
		# self.w.rightGlyphList.getNSScrollView().setBorderType_(NSNoBorder)

		self.w.lblMessage = TextBox((10, 10, -10, 17), text = 'Make pairs from selection', sizeStyle = 'regular')


		shY = -30
		posYcontrols = glyphCollectionShiftY - 37
		elemH = 19
		leftX = 10
		leftHalfX = (wW / 4) + 4
		wx1 = (wW / 4) - 12
		wx2 = (wW / 4) - 6
		wxfull1 = (wW / 2) - 12
		rightX = (wW / 2) + 2
		rightHalfX = (wW / 2) + (wW / 4) - 4
		wxfull2 = -10

		blockStep = 23
		blockY1 = hW - posYcontrols + shY
		posYcontrols -= blockStep
		blockY2 = hW - posYcontrols + shY
		posYcontrols -= blockStep
		blockY3 = hW - posYcontrols + shY
		posYcontrols -= blockStep
		blockY4 = hW - posYcontrols + shY
		posYcontrols -= blockStep
		blockY5 = hW - posYcontrols + shY
		posYcontrols -= blockStep*2
		blockY6 = hW - posYcontrols + shY

		self.w.btnGetLeft = Button((leftX, blockY1, wx1, elemH),
		                           "Add Left glyphs",
		                           callback = self.btnAddGlyphs2ListCallback,
		                           sizeStyle = 'small')
		self.w.btnDelLeft = Button((leftHalfX, blockY1, wx2, elemH),
		                           "Remove Left glyphs",
		                           callback = self.btnDeleteGlyphsFromListCallback,
		                           sizeStyle = 'small')

		self.w.btnCompressGroupsLeft = Button((leftX, blockY2, wx1, elemH),
		                           "Compress Left",
		                           callback = self.btnCompressExpandCallback,
		                           sizeStyle = 'small')
		self.w.btnExpandGroupsLeft = Button((leftHalfX, blockY2, wx2, elemH),
		                                      "Expand Left",
		                                      callback = self.btnCompressExpandCallback,
		                                      sizeStyle = 'small')

		self.w.btnGetRight = Button((rightX, blockY1, wx1, elemH),
		                            "Add Right glyphs",
		                            callback = self.btnAddGlyphs2ListCallback,
		                            sizeStyle = 'small')
		self.w.btnDelRight = Button((rightHalfX, blockY1, wx2, elemH),
		                            "Remove Right glyphs",
		                            callback = self.btnDeleteGlyphsFromListCallback,
		                            sizeStyle = 'small')

		self.w.btnCompressGroupsRight = Button((rightX, blockY2, wx1, elemH),
		                            "Compress Right",
		                            callback = self.btnCompressExpandCallback,
		                            sizeStyle = 'small')
		self.w.btnExpandGroupsRight = Button((rightHalfX, blockY2, wx2, elemH),
		                                       "Expand Right",
		                                       callback = self.btnCompressExpandCallback,
		                                       sizeStyle = 'small')

		self.w.textPatternLeft = EditText((leftX, blockY3, wxfull1, elemH),
		                                  text = pLefttext,
		                                  sizeStyle = 'small')
		self.w.textPatternRight = EditText((rightX, blockY3, wxfull2, elemH),
		                                   text = pRighttext,
		                                   sizeStyle = 'small')

		self.w.btnLeftSaveSet = Button((leftX, blockY4, wx1, elemH), "Save Left set...",
		                          callback = self.btnLeftSaveSetCallback, sizeStyle = 'small')
		self.w.btnLeftLoadSet = Button((leftHalfX, blockY4, wx2, elemH), "Load Left set...",
		                         callback = self.btnLeftLoadSetCallback, sizeStyle = 'small')

		self.w.btnRightSaveSet = Button((rightX, blockY4, wx1, elemH), "Save Right set...",
		                          callback = self.btnRightSaveSetCallback, sizeStyle = 'small')
		self.w.btnRightLoadSet = Button((rightHalfX, blockY4, wx2, elemH), "Load Right set...",
		                         callback = self.btnRightLoadSetCallback, sizeStyle = 'small')

		wSeg = wx1/8
		segmentsGrp = [{'width': wSeg, 'title': '1'},
		               {'width': wSeg, 'title': '2'},
		               {'width': wSeg, 'title': '3'},
		               {'width': wSeg, 'title': '4'},
		               {'width': wx1 - (wSeg)*4, 'title': 'Pairs/Line'}]
		self.w.btnPairsPerLine = SegmentedButton((rightHalfX, blockY5, wx1+6, elemH),
		                                     segmentDescriptions = segmentsGrp,
		                                     selectionStyle = 'one',
		                                     sizeStyle = 'small',
		                                    callback = self.btnPairsPerLineCallback)
		self.w.btnPairsPerLine.set(4)

		# self.w.checkBoxOnePairPerLine = CheckBox((rightX,blockY4,wx1,elemH),title = 'One Pair per Line',value = False,sizeStyle = 'small')
		self.w.checkTouchesOnly = CheckBox((rightX, blockY5, wx1, elemH), title = 'Show Touches only',value = False, sizeStyle = 'small')

		self.w.btnCancel = Button((leftX, blockY6, wx1, elemH), "Cancel",
		                          callback = self.btnCloseCallback, sizeStyle = 'small')
		# self.w.btnTouches = Button((rightX, blockY5, wx1, elemH), "Touches only",
		#                          callback = self.btnCloseCallback, sizeStyle = 'small')
		self.w.btnApply = Button((rightHalfX, blockY6, wx2, elemH), "Apply",
		                         callback = self.btnCloseCallback, sizeStyle = 'small')
		self.w.progressBar = ProgressBar((leftHalfX+3, blockY6, wx1+wx2-2, elemH),sizeStyle = 'small')

		self.setViewGlyphsCell(self.leftList,direction = 'L')
		self.setViewGlyphsCell(self.rightList,direction = 'R')
		self.w.open()

	# def exceptionSelectorCallback (self, sender):
	# 	print self.listExt[sender.get()]

	def btnPairsPerLineCallback(self, sender):
		ppl = sender.get()
		if ppl == 4:
			self.pairsPerLine = None
		else:
			self.pairsPerLine = ppl+1
		# print 'Set PairsPerLine', self.pairsPerLine

	def btnCompressExpandCallback(self, sender):
		if sender == self.w.btnCompressGroupsLeft:
			self.compressGlyphsList(direction = 'L')
		elif sender == self.w.btnCompressGroupsRight:
			self.compressGlyphsList(direction = 'R')
		elif sender == self.w.btnExpandGroupsLeft:
			self.expandGlyphsList(direction = 'L')
		elif sender == self.w.btnExpandGroupsRight:
			self.expandGlyphsList(direction = 'R')

	def compressGlyphsList(self, direction):
		glyphs = []
		groups = []
		groupdic = {}
		if direction == 'L':
			for idx in self.w.leftGlyphList.getSelection():
				glyphs.append((self.leftList[idx],idx))
			# for name in glyphs:
			# 	self.leftList.remove(name)
		elif direction == 'R':
			for idx in self.w.rightGlyphList.getSelection():
				glyphs.append((self.rightList[idx],idx))
			# for name in glyphs:
			# 	self.rightList.remove(name)

		for (name,idx) in glyphs:
			groupname = self.hashKernDic.getGroupNameByGlyph(name, direction)
			if self.hashKernDic.thisGroupIsMMK(groupname):
				if direction == 'L':
					tl = []
					if self.font.groups[groupname][0] in self.leftList:
						idx = self.leftList.index(self.font.groups[groupname][0])
					for rn in self.leftList:
						if groupname == self.hashKernDic.getGroupNameByGlyph(rn, direction):
							tl.append(rn)
					for rn in tl:
						if self.font.groups[groupname][0]!=rn:
							self.leftList.remove(rn)
				if direction == 'R':
					tl = []
					if self.font.groups[groupname][0] in self.rightList:
						idx = self.rightList.index(self.font.groups[groupname][0])
					for rn in self.rightList:
						if groupname == self.hashKernDic.getGroupNameByGlyph(rn, direction):
							tl.append(rn)
					for rn in tl:
						if self.font.groups[groupname][0] != rn:
							self.rightList.remove(rn)
				if groupname not in groupdic and len(self.font.groups[groupname])>0:
					groupdic[groupname] = (self.font.groups[groupname][0],idx)
			else:
				if name not in groupdic:
					groupdic[name] = (name,idx)

		if direction == 'L':
			for key, (name,idx) in groupdic.items():
				if name not in self.leftList:
					self.leftList.insert(idx, name)
			# self.leftList = sorted(self.leftList)
			self.setViewGlyphsCell(self.leftList, direction = direction)
		elif direction == 'R':
			for key, (name,idx) in groupdic.items():
				if name not in self.rightList:
					self.rightList.insert(idx, name)
			# self.rightList = sorted(self.rightList)
			self.setViewGlyphsCell(self.rightList, direction = direction)



	def expandGlyphsList(self, direction):
		glyphs = []
		groups = []

		if direction == 'L':
			for idx in self.w.leftGlyphList.getSelection():
				glyphs.append(self.leftList[idx])
		elif direction == 'R':
			for idx in self.w.rightGlyphList.getSelection():
				glyphs.append(self.rightList[idx])

		for name in glyphs:
			groupname = self.hashKernDic.getGroupNameByGlyph(name, direction)
			if self.hashKernDic.thisGroupIsMMK(groupname):
				groups.append(groupname)

		for groupname in groups:
			content = self.font.groups[groupname]
			if direction == 'L':
				for gname in content:
					if gname not in self.leftList:
						self.leftList.append(gname)
			elif direction == 'R':
				for gname in content:
					if gname not in self.rightList:
						self.rightList.append(gname)

		if direction == 'L':
			self.setViewGlyphsCell(self.leftList, direction = direction)
		elif direction == 'R':
			self.setViewGlyphsCell(self.rightList, direction = direction)

	def setViewGlyphsCell(self, glyphslist, direction):
		glyphs = []

		if direction == 'L':
			self.w.leftGlyphList.set([])
			for name in glyphslist:
				if name in self.font:
					glyphs.append(self.font[name])
			self.w.leftGlyphList.set(glyphs)
		elif direction == 'R':
			self.w.rightGlyphList.set([])

			for name in glyphslist:
				if name in self.font:
					glyphs.append(self.font[name])
			self.w.rightGlyphList.set(glyphs)

	def btnAddGlyphs2ListCallback (self, sender):
		if sender == self.w.btnGetLeft:
			for name in self.font.selection:
				if name not in self.leftList:
					self.leftList.append(name)
			self.setViewGlyphsCell(self.leftList, direction = 'L')
		elif sender == self.w.btnGetRight:
			for name in self.font.selection:
				if name not in self.rightList:
					self.rightList.append(name)
			self.setViewGlyphsCell(self.rightList, direction = 'R')

	def btnDeleteGlyphsFromListCallback(self, sender):
		glyphs = []
		if sender == self.w.btnDelLeft:
			for idx in self.w.leftGlyphList.getSelection():
				glyphs.append(self.leftList[idx])
			for name in glyphs:
				self.leftList.remove(name)
			self.setViewGlyphsCell(self.leftList, direction = 'L')
		elif sender == self.w.btnDelRight:
			for idx in self.w.rightGlyphList.getSelection():
				glyphs.append(self.rightList[idx])
			for name in glyphs:
				self.rightList.remove(name)
			self.setViewGlyphsCell(self.rightList, direction = 'R')


	def groupsDropCallback (self, sender, dropInfo):

		if dropInfo['isProposal']: pass

		else:
			# print sender, dropInfo
			dest = sender.id
			source = dropInfo['source']
			try:
				source = source.id
			except:
				print ('except', source)
				return True
			# print '='*80
			idx = dropInfo['rowIndex']

			glyphlist = [glyph.name for glyph in dropInfo['data']]
			# print glyphlist
			if not glyphlist: return True

			if source == dest and source == 'leftgroup':
				direction = 'L'
				# print 'for left group, insert before', self.leftList[idx]
				glyphIdxName = self.leftList[idx]
				for name in glyphlist:
					self.leftList.remove(name)
				idx = 0
				for i, name in enumerate(self.leftList):
					if name == glyphIdxName:
						idx = i
				for name in glyphlist:
					self.leftList.insert(idx, name)
					idx +=1
				self.setViewGlyphsCell(self.leftList,direction = direction)

			if source == dest and source == 'rightgroup':
				direction = 'R'
				# print 'for right group, insert before', self.rightList[idx]
				glyphIdxName = self.rightList[idx]
				for name in glyphlist:
					self.rightList.remove(name)
				idx = 0
				for i, name in enumerate(self.rightList):
					if name == glyphIdxName:
						idx = i
				for name in glyphlist:
					self.rightList.insert(idx, name)
					idx += 1
				self.setViewGlyphsCell(self.rightList, direction = direction)

		return True

	def mixPairs(self):
		self.patternLeft = tdGlyphparser.translateText(font = self.font,
		                                               text = self.w.textPatternLeft.get())
		self.patternRight = tdGlyphparser.translateText(font = self.font,
		                                                text = self.w.textPatternRight.get())
		# if not self.pairsPerLine and not self.w.checkTouchesOnly.get():
		if not self.w.checkTouchesOnly.get():
		# if not self.w.checkBoxOnePairPerLine.get() and not self.w.checkTouchesOnly.get():
			self.callback(self.patternLeft, self.leftList,
		              self.rightList, self.patternRight, command = 'lines', pairsperline = self.pairsPerLine)
		else:
			line = ''
			LPattern = ''
			RPattern = ''
			if self.patternLeft:
				for l in self.patternLeft:
					if l != '':
						LPattern += '/%s' % l
			if self.patternRight:
				for r in self.patternRight:
					if r != '':
						RPattern += '/%s' % r
			countPair = 0

			totalpairs = len(self.leftList)*len(self.rightList)
			# self.w.progressBar._nsObject.setMinValue_(0)
			# self.w.progressBar._nsObject.setMaxValue_(totalpairs)
			perc = totalpairs/100
			pairsCountProgress = 0
			# print 'total pairs:', totalpairs
			for glyph_left in self.leftList:
				for glyph_right in self.rightList:
					pairsCountProgress +=1
					if round(perc,0) == pairsCountProgress:
						self.w.progressBar.increment()
						pairsCountProgress = 0
					if self.w.checkTouchesOnly.get():
						pairinfo = researchPair(self.font, self.hashKernDic, (glyph_left, glyph_right))
						kernValue = pairinfo['kernValue']
						if kernValue == None:
							kernValue = 0
						if checkOverlapingGlyphs(self.font, self.font[glyph_left], self.font[glyph_right], kernvalue = kernValue):
							line += '%s/%s/%s%s' % (LPattern, glyph_left, glyph_right, RPattern)
							countPair += 1
							if countPair == self.pairsPerLine:
								line += '\\n'
								countPair = 0
							# else:
							# 	countPair += 1
					# else:
					# 	line += '%s/%s/%s%s' % (LPattern, glyph_left, glyph_right, RPattern)
					# 	countPair += 1
					# 	if countPair == self.pairsPerLine:
					# 		line += '\\n'
					# 		countPair = 0
						# else:
						# 	countPair += 1

					# if self.w.checkBoxOnePairPerLine.get():
					# 	line += '\\n'
			# print 'pairs maked:', pairsCountProgress
			self.callback(self.patternLeft, self.leftList,
			              self.rightList, self.patternRight,text = line,
			              command = 'glyphsready')


	# def mixOverlapingPairs(self):
	# 	self.patternLeft = tdGlyphparser.translateText(font = self.font,
	# 	                                               text = self.w.textPatternLeft.get())
	# 	self.patternRight = tdGlyphparser.translateText(font = self.font,
	# 	                                                text = self.w.textPatternRight.get())
	# 	tleft = []
	# 	tright = []
	# 	line = ''
	# 	LPattern = ''
	# 	RPattern = ''
	# 	if self.patternLeft:
	# 		for l in self.patternLeft:
	# 			if l != '':
	# 				LPattern += '/%s' % l
	# 	if self.patternRight:
	# 		for r in self.patternRight:
	# 			if r != '':
	# 				RPattern += '/%s' % r
	#
	# 	for glyph_left in self.leftList:
	# 		for glyph_right in self.rightList:
	# 			pairinfo = researchPair(self.font, self.hashKernDic, (glyph_left, glyph_right))
	# 			kernValue = pairinfo['kernValue']
	# 			if kernValue == None:
	# 				kernValue = 0
	#
	# 			if checkOverlapingGlyphs(self.font[glyph_left], self.font[glyph_right], kernvalue = kernValue):
	#
	# 				line += '%s/%s/%s%s' % (LPattern,glyph_left, glyph_right,RPattern)
	# 				if self.w.checkBoxOnePairPerLine.get():
	# 					line +='\\n'
	# 	self.callback(self.patternLeft, self.leftList, self.rightList, self.patternRight,text = line, command = 'glyphsready')



	def btnCloseCallback (self, sender):
		if sender == self.w.btnApply:
			self.mixPairs()
		self.w.leftGlyphList.set([])
		self.w.rightGlyphList.set([])
		self.w.close()

		# elif sender == self.w.btnTouches:
		# 	self.mixOverlapingPairs()


	def loadSetOfGlyphs (self, filename, direction):
		print ('Loading glyph set from', filename)
		glyphset = []
		gfile = open(filename, mode = 'r')
		for line in gfile:
			line = line.strip()
			line = line.split(' ')
			glyphset.extend(line)
		gfile.close()
		glyphs = []
		for gname in glyphset:
			if gname in self.font:
				if direction == 'L':
					self.leftList.append(gname)
				else:
					self.rightList.append(gname)
				glyphs.append(self.font[gname])
			if direction == 'L':
				self.w.leftGlyphList.set(glyphs)
			else:
				self.w.rightGlyphList.set(glyphs)


	def saveSetOfGlyphs(self, filename, direction):
		glyphs = []
		print ('Saving glyphs set to', filename)

		if direction == 'L':
			for glyph in self.w.leftGlyphList.get():
				glyphs.append(glyph.name)
		else:
			for glyph in self.w.rightGlyphList.get():
				glyphs.append(glyph.name)			# glyphset = ' '.join(self.w.rightGlyphList.get())
		glyphset = ' '.join(glyphs)

		gfile = open(filename, mode = 'w')
		gfile.write(glyphset)
		gfile.close()
		print ('File saved.')


	def btnLeftSaveSetCallback(self, sender):
		filename = putFile(messageText = 'Save glyphs set file', title = 'title')
		if filename:
			self.saveSetOfGlyphs(filename = filename, direction = 'L')

	def btnLeftLoadSetCallback(self, sender):
		filename = getFile(messageText = 'Select text file', title = 'title')
		if filename and filename[0]:
			self.loadSetOfGlyphs(filename = filename[0], direction = 'L')

	def btnRightSaveSetCallback(self, sender):
		filename = putFile(messageText = 'Save glyphs set file', title = 'title')
		if filename:
			self.saveSetOfGlyphs(filename = filename, direction = 'R')

	def btnRightLoadSetCallback(self, sender):
		filename = getFile(messageText = 'Select text file', title = 'title')
		if filename and filename[0]:
			self.loadSetOfGlyphs(filename = filename[0], direction = 'R')


	# def draw (self):
	# 	self.w.rightGlyphList.preloadGlyphCellImages()
	# 	self.w.leftGlyphList.preloadGlyphCellImages()
