import sys
# from math import *
import math
from vanilla import *
from mojo.UI import *
from fontParts.world import CurrentFont, RGlyph
from defconAppKit.windows.baseWindow import BaseWindowController
from mojo.drawingTools import *
from mojo.glyphPreview import GlyphPreview
from fontTools.pens.cocoaPen import CocoaPen
from mojo.canvas import Canvas
from defconAppKit.controls.glyphCollectionView import GlyphCollectionView
from AppKit import *
from mojo.drawingTools import *
# from lib.UI.fontOverView.speedGlyphCollectionView import SpeedGlyphCollectionView
from mojo.events import addObserver, removeObserver

from mojo.canvas import Canvas

from mojo.drawingTools import *
# from robofab.world import CurrentFont
# from vanilla.nsSubclasses import getNSSubclass
from defconAppKit.windows import *

import importlib
import tdGroupViews
importlib.reload(tdGroupViews)
from tdGroupViews import TDGroupViewStacked

import tdKernToolEssentials
importlib.reload(tdKernToolEssentials)
from tdKernToolEssentials import *


#

def calculateHeightOfControl(font, groupname, baseHeight = 101):
	a = len(font.groups[groupname])
	y1 = 0
	if a > 10:
		y1 = ((a - 10) / 10)
		# print y1
		d, v = math.modf(y1)
		# print d , int(v)
		y1 = int(v) * 100
		if d <= .5:
			y1 += 50
		elif d > .5:
			y1 += 100
	baseHeight += y1
	return baseHeight


class TDGroupViewCell(VanillaBaseObject):
	nsViewClass = NSView

	# def __init__ (self, posSize, font=None, groupname=None, groupsChangedCallback = None):
	def __init__ (self, posSize, groupsChangedCallback = None, selectionCallback = None):

		xw, yw, tx, ty = posSize
		y = 101
		self._posSize = (xw, yw, tx, y)
		self._setupView(self.nsViewClass, (xw, yw, tx, y)) #101))  # (0, 0, -0, 106)

		self.groupsChangedCallback = groupsChangedCallback
		self.selectionCallback = selectionCallback
		self.groupname = None
		self.heightOfControl = y
		xpos = -110
		xGC = 0
		xm = -105

		self.keyGlyphView = TDGroupViewStacked((xpos, 0, 100, 101),selectionCallback = self.selectGroupView, liveupdate = True, sizeStyle = 'big')
		dropSettings = dict(callback = self.groupsDropCallback)
		self.groupView = GlyphCollectionView((xGC, 0, xm-17, y-1 ), #117),
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
		                                     doubleClickCallback = self.doubleClickCallback,
		                                          selectionCallback = self.selectGroupView

		)

		self.groupView.setCellRepresentationArguments(drawHeader = True)  # , drawMetrics = True
		self.groupView.setCellSize((47, 50))
		# self.groupView.getNSScrollView().setHasVerticalScroller_(False)
		# self.groupView.getNSScrollView().setHasHorizontalScroller_(False)
		#
		# self.groupView.getNSScrollView().setAutohidesScrollers_(False)
		# self.groupView.getNSScrollView().setDrawsBackground_(False)
		# self.groupView.getNSScrollView().setBackgroundColor_(NSColor.whiteColor())

		# self.groupView.getNSScrollView().setBorderType_(NSNoBorder)



	def selectGroupView(self, info):
		if self.selectionCallback:
			self.selectionCallback(self.groupname)


	def selected(self, selected = False):
		self.keyGlyphView.selected(selected)
		if not selected:
			self.groupView.setSelection([])


	def doubleClickCallback(self, sender):
		glist = []
		for gindex in self.groupView.getSelection():
			glist.append(self.groupView[gindex].name)
		w = OpenSpaceCenter(CurrentFont())
		w.set(glist)


	def groupsDropCallback (self, sender, dropInfo):
		# print sender, dropInfo
		# groupper(sender, dropInfo)
		if dropInfo['isProposal']: pass
		else:
			dest = sender.id
			source = dropInfo['source']
			try:
				sourceid = source.id
			except:
				print (source)
				sourceid = None
			glist = []
			for glyph in dropInfo['data']:
				glist.append(glyph.name) #= dropInfo['data']

			updateGroups = False
			groupsChanged = []
			if sourceid != dest:
				if sourceid == 'fontview' and dest != 'fontview':
					addGlyphsToGroup(self._font, dest, glist)
					groupsChanged = [ dest, sourceid ]
					updateGroups = True

				elif sourceid != 'fontview' and dest == 'fontview':
					delGlyphsFromGroup(self._font, sourceid, glist)
					groupsChanged = [ dest, sourceid ]
					updateGroups = True

				elif sourceid != 'fontview' and dest != 'fontview':
					delGlyphsFromGroup(self._font, sourceid, glist)
					addGlyphsToGroup(self._font, dest, glist)
					groupsChanged = [ sourceid, dest ]
					updateGroups = True

			elif sourceid == dest:
				idx = dropInfo['rowIndex']
				repositionGlyphsInGroup(self._font, dest, idx, glist)
				groupsChanged = [ dest, sourceid ]
				updateGroups = True

			if updateGroups and self.groupsChangedCallback:
				self.groupsChangedCallback(groupsChanged)

		return True


	def setFont(self, font):
		self._font = font


	def setPositionY(self,posSize):
		y = calculateHeightOfControl(self._font, groupname = self.groupname, baseHeight = 101) + 16
		xw, yw, tx, ty = posSize
		self.setPosSize((xw, yw, tx, y))
		self.groupView.setPosSize((0, 0, -105 - 17, y - 17))
		self.heightOfControl = y


	def setGroupView (self, font, groupname):
		self.setFont(font)
		self.groupname = groupname
		self.direction = getDirection(groupname)
		self.groupView.id = groupname

		self.setPositionY(self._posSize)

		self.keyGlyphView.setFont(self._font)
		self.keyGlyphView.setGroupStack(self.groupname)
		self.groupView.set(self.keyGlyphView.glyphsToDisplay)
		# print (self.keyGlyphView.glyphsToDisplay)

		# d = []
		# for g in self.keyGlyphView.glyphsToDisplay:
		# 	d.append(g)
		# self.groupView.set(d)
		# self.setPositionY(self._posSize)

	def clear (self):
		self.groupView.set([])




class TDGroupsCollectionView(VanillaBaseObject):
	nsViewClass = NSView

	def __init__ (self, posSize, font=None, direction='L',
	              groupsChangedCallback = None, selectionCallback = None,
	              groupPrefix = ID_KERNING_GROUP):
		xw, yw, tx, ty = posSize
		self._tx = tx
		self._setupView(self.nsViewClass, posSize)  # (0, 0, -0, 106)
		self._font = font
		self.groupPrefix = groupPrefix
		self.groupsChangedCallback = groupsChangedCallback
		self.selectionCallback = selectionCallback
		self._listObjGroups = {}
		self._buildingView = True

		self.groupsList = []
		self.direction = direction
		self.currentGroupName = None

		self.view = Group((0, 0, -0, 1000000))
		self.scroll = ScrollView((0, 30, -5, -20), self.view.getNSView())
		# self.progressBar = ProgressBar((0,-15,-5,-5),sizeStyle = 'small',isIndeterminate = True)
		# self.progressBar.show(False)
		self.buildView(self.direction)


	def buildView(self, direction):

		if self.direction != direction:
			self.clear()

		self.direction = direction
		y = 5
		self._buildingView = True
		# totalgroups = len(self._font.groups)
		# perc = totalgroups / 100
		# pairsCountProgress = 0
		# self.progressBar.set(0)
		# self.progressBar.start()
		# self.progressBar.show(True)

		self.view.show(False)
		# groupList = sortGroupsByGlyphOrder(self._font,self.direction)
		for idx, groupname in enumerate(sorted(self._font.groups.keys())):
		# for idx, groupname in enumerate(groupList):

			# pairsCountProgress += 1
			# if round(perc, 0) == pairsCountProgress:
			# 	# self.progressBar.increment()
			# 	pairsCountProgress = 0
			if groupname.startswith(self.groupPrefix):
				if (self.direction == 'L' and ID_GROUP_DIRECTION_POSITION_LEFT in groupname) \
						or (self.direction == 'R' and ID_GROUP_DIRECTION_POSITION_RIGHT in groupname):
					if groupname not in self._listObjGroups:
						objName = "grCtrl_%s" % getUniqName()
						setattr(self.view, objName,
						        TDGroupViewCell((5, y, self._tx - 33, 0),
						                    groupsChangedCallback = self.groupsChanged,
						                    selectionCallback = self.selectedGroup))
						self.view.__getattribute__(objName).setGroupView(self._font, groupname)
						# self.groupsList.append(getDisplayNameGroup(groupname))
						self._listObjGroups[groupname] = {'nameObj': objName,
						                                  'posY': y,
						                                  'shortNameGroup': getDisplayNameGroup(groupname),
						                                  'direction': direction}
					# obj = getattr(self.view, self._listObjNames[idx])
					# obj.setGroupView(self._font, groupname)
		# self.groupsList = sorted(self.groupsList) #sortGroupsByGlyphOrder(self._font,self.direction, shortnames = True)
		self._buildingView = False
		self.view.show(True)
		self.repositionGroupViews()
		# self.progressBar.set(0)
		# self.progressBar.show(False)
		# self.progressBar.stop()

	def deleteGroupViewByName(self, groupname):
		if groupname in self._listObjGroups:
			prevIdx = 0
			idx = 0
			# for gname in sortGroupsByGlyphOrder(self._font,self.direction):
			for gname, obj in sorted(self._listObjGroups.items()):
				if gname == groupname:
					delattr(self.view, self._listObjGroups[gname]['nameObj'])
					self._listObjGroups.pop(groupname)
					del self._font.groups[groupname]

					prevIdx = idx - 1
					if prevIdx < 0:
						prevIdx = 0

					self.buildView(self.direction)
				idx += 1
			idx = 0

			# for gname in sortGroupsByGlyphOrder(self._font, self.direction):
			for gname, obj in sorted(self._listObjGroups.items()):
				if idx == prevIdx:
					self.scrollToGroup(gname)
					self.currentGroupName = gname
					self.groupsChangedCallback(self)
					return
				idx +=1

		# for objname in self._listObjGroups:
		# 	if self.view.__getattribute__(objname).groupname == groupname:
		# 		delattr(self.view, objname)
		# 		self._listObjNames.remove(objname)
		# 		self._listController.pop(groupname)
		# 		self.groupsList.remove(getDisplayNameGroup(groupname))
		# 		return


	def clear(self):
		if self._listObjGroups:
			for gN, obj in self._listObjGroups.items():
				self.view.__getattribute__(obj['nameObj']).clear()
				delattr(self.view, obj['nameObj'])
			self._listObjGroups = {}
			self.groupsList = []


	def scrollToGroup (self, groupName=None):
		if groupName:
			if groupName in self._listObjGroups.keys():
				point = NSPoint(0, self._listObjGroups[groupName]['posY'])
			else:
				groupName = None
				point = NSPoint(0, 0)
		else:
			point = NSPoint(0, 0)
		self.scroll.getNSScrollView().contentView().scrollToPoint_(point)
		self.scroll.getNSScrollView().reflectScrolledClipView_(self.scroll.getNSScrollView().contentView())
		self.currentGroupName = groupName


	def repositionGroupViews(self):
		y = 5
		# for gN in sortGroupsByGlyphOrder(self._font, self.direction):
		# 	# obj = self._listObjGroups[gN]
		# 	self.view.__getattribute__(self._listObjGroups[gN]['nameObj']).setPositionY((5, y, self._tx - 33, 0))
		# 	self._listObjGroups[gN]['posY'] = (0 - y) + 5
		# 	y += self.view.__getattribute__(self._listObjGroups[gN]['nameObj']).heightOfControl - 5
		gl = []
		for gN, obj in sorted(self._listObjGroups.items()):
			self.view.__getattribute__(obj['nameObj']).setPositionY((5,y,self._tx - 33, 0))
			self._listObjGroups[gN]['posY'] = (0 - y) + 5
			gl.append(getDisplayNameGroup(gN))
			y += self.view.__getattribute__(obj['nameObj']).heightOfControl -5

		self.groupsList = gl
		self.view.setPosSize((0, 0, -0, y))
		frame = self.scroll.getNSScrollView().contentView().frame()
		self.view._setFrame(frame)
		self.scrollToGroup(self.currentGroupName)


	def selectedGroup(self, info):
		if self._buildingView: return
		for gN, obj in self._listObjGroups.items():
			if gN == info:
				self.view.__getattribute__(obj['nameObj']).selected(True)
				self.currentGroupName = info
			else:
				self.view.__getattribute__(obj['nameObj']).selected(False)
		if self.selectionCallback:
			self.selectionCallback(info)


	def groupsChanged(self, info):
		if info:
			self.currentGroupName = info[0]
			for groupname in info:
				if groupname in self._listObjGroups:
					self.view.__getattribute__(self._listObjGroups[groupname]['nameObj']).setGroupView(self._font, groupname)
			self.repositionGroupViews()
			self.selectedGroup(self.currentGroupName)
			self.groupsChangedCallback(self)

	def updateGroupView(self, groupname):
		if groupname:
			self.groupsChanged([groupname])

	def refresh(self):
		self.buildView(self.direction)
		self.groupsChangedCallback(self)


class TDFontView(VanillaBaseObject):
	nsViewClass = NSView
	def __init__ (self, posSize, font=None, hideGrouped = True, direction = 'L',
	              groupsChangedCallback = None, groupPrefix = '.MRX'):
		xw, yw, tx, ty = posSize
		self._setupView(self.nsViewClass, posSize)  # (0, 0, -0, 106)
		self._font = font
		self.groupsChangedCallback = groupsChangedCallback
		xpos = 0
		xGC = 105
		xm = -0
		self.hideGrouped = hideGrouped
		self.direction = direction
		self.groupPrefix = groupPrefix
		dropSettings = dict(callback = self.groupsDropCallback)
		self.hashKernDic = TDHashKernDic(font)

		self.fontView = GlyphCollectionView((xpos, yw, tx, ty),
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
		                                         doubleClickCallback = self.doubleClickCallback
		                                         )
		self.fontView.id = 'fontview'

		self.fontView.setCellRepresentationArguments(drawHeader = True, drawMetrics = True)  # , drawMetrics = True
		# self.fontView.getNSScrollView().setHasVerticalScroller_(True)
		# self.fontView.getNSScrollView().setHasHorizontalScroller_(False)
		#
		# self.fontView.getNSScrollView().setAutohidesScrollers_(False)
		# self.fontView.getNSScrollView().setBackgroundColor_(NSColor.whiteColor())
		# self.fontView.getNSScrollView().setBorderType_(NSNoBorder)
		# addObserver(self.fontView, "draw", "glyphCellDraw")
		self.fontView.setCellSize((70,70))
		self.setFontView()


	def doubleClickCallback(self, sender):
		w = OpenSpaceCenter(CurrentFont())
		w.set(self.getSelectedGlyphs())


	def groupsDropCallback (self, sender, dropInfo):
		if dropInfo['isProposal']: pass
		else:
			dest = sender.id
			source = dropInfo['source']
			try:
				sourceid = source.id
			except:
				print (source)
				sourceid = None
			glist = []
			for glyph in dropInfo['data']:
				glist.append(glyph.name)  # = dropInfo['data']

			updateGroups = False
			groupName = None
			if sourceid != dest:
				# if sourceid == 'fontview' and dest != 'fontview':
				# 	addGlyphsToGroup(self._font, dest, glist)
				# 	print 'fontview F G', dest, sourceid
				#
				# 	groupName = dest
				# 	updateGroups = True

				if sourceid != 'fontview' and dest == 'fontview':
					# WORKS ONLY ONE
					delGlyphsFromGroup(self._font, sourceid, glist)
					# print 'fontview G F', dest, sourceid
					groupName = sourceid
					updateGroups = True
				#
				# elif sourceid != 'fontview' and dest != 'fontview':
				# 	delGlyphsFromGroup(self._font, sourceid, glist)
				# 	addGlyphsToGroup(self._font, dest, glist)
				# 	print 'fontview G G', dest, sourceid
				# 	groupName = dest
				# 	updateGroups = True

			if updateGroups and self.groupsChangedCallback:
				self.groupsChangedCallback(groupName)
		return True


	def isGlyphNotInGroups(self, glyphname):
		for group, content in self._font.groups.items():
			if group.startswith(self.groupPrefix):
				if self.direction == 'L' and ID_GROUP_DIRECTION_POSITION_LEFT in group:
					if glyphname in content:
						return False
				if self.direction == 'R' and ID_GROUP_DIRECTION_POSITION_RIGHT in group:
					if glyphname in content:
						return False
		return True


	def setFontView(self):
		glyphs = []
		for glyphname in self._font.glyphOrder:
			if self.hideGrouped:
				if self.isGlyphNotInGroups(glyphname):
					glyphs.append(self._font[glyphname])
			else:
				glyphs.append(self._font[glyphname])
		self.fontView.set(glyphs)

	def getSelectedGlyphs(self):
		glist = []
		for gindex in self.fontView.getSelection():
			glist.append(self.fontView[gindex].name)
		return glist

	def clear(self):
		self.fontView.set([])


if __name__ == "__main__":
	class MyW(object):
		def __init__ (self):

			self.w = Window((995, 600), "KernGroups", minSize = (995, 400), maxSize = (995,2500))
			self.groupPrefix = ID_KERNING_GROUP
			self.direction = 'L'
			self.font = CurrentFont()
			self.w.cbGroupsList = PopUpButton((-240, 5, -5, 21), {}, callback = self.cbGroupsListCallback, sizeStyle = 'regular')

			self.w.fontView = TDFontView((5,15,580,-50),
			                             font = self.font,
			                             groupsChangedCallback = self.groupsChanged,
			                             groupPrefix = self.groupPrefix)
			self.w.groupsView = TDGroupsCollectionView((590, 0, 405, -0),
			                                           font = CurrentFont(),
			                                           direction = self.direction,
			                                           groupsChangedCallback = self.hideGroupedCallback,
			                                           groupPrefix = self.groupPrefix,
			                                           selectionCallback = self.selectionGroup
			                                    )
			segments = [{'width': 54, 'title': 'Left'}, {'width': 54, 'title': 'Right'}]
			self.w.btnSwitchLeftRight = SegmentedButton((590, 3, 120, 23),
			                                          segmentDescriptions = segments,
			                                          selectionStyle = 'one',  # sizeStyle = 'mini', #48
			                                          callback = self.btnSwitchLeftRightCallback,
			                                            sizeStyle = 'regular')
			# self.modeLeftRight = 0
			self.w.btnSwitchLeftRight.set(0)

			ypos = -90
			self.w.btnMakeGroup = Button((10, ypos, 150, 21),title = 'Make Group', callback = self.makeGroup)
			self.w.btnMakeGroups = Button((10, ypos + 25, 150, 21),title = 'Make Groups', callback = self.makeGroups)

			# self.w.btnFixMarginsGlobal = Button((420, ypos, 150, 21), title = 'Fix Margins', callback = self.fixMarginsGlobal)
			# ypos += 25
			self.w.btnDeleteGroup = Button((420, ypos , 150, 21), title = 'Delete Group', callback = self.deleteGroup)

			self.w.btnRefresh = Button((420, ypos + 25, 150, 21), title = 'Refresh', callback = self.refreshCallback)
			self.w.chbHideGrouped = CheckBox((10,-30, 150, 21),
			                                 title = 'Hide grouped',
			                                 value = True, callback = self.hideGroupedCallback)
			self.w.cbGroupsList.setItems(self.w.groupsView.groupsList)
			self.w.bind('close', self.windowCloseCallback)
			self.w.open()

		def windowCloseCallback(self, sender):
			self.w.groupsView.clear()
			self.w.fontView.clear()

		def hideGroupedCallback(self, sender):

			self.w.fontView.direction = self.direction
			self.w.fontView.hideGrouped = self.w.chbHideGrouped.get()
			self.w.fontView.groupPrefix = self.groupPrefix
			self.w.fontView.setFontView()

		def selectionGroup(self, info):
			if info:
				self.w.cbGroupsList.setItem(getDisplayNameGroup(info))


		def directionChangedCallback(self, sender):
			self.hideGroupedCallback(self.w.chbHideGrouped)


		def cbGroupsListCallback(self, sender):
			groupname = getGroupNameFromDisplayName(sender.getItems()[sender.get()],direction = self.direction)
			self.w.groupsView.scrollToGroup(groupname)
			self.w.groupsView.selectedGroup(groupname)
			# self.w.cbGroupsList.setItem(sender.getItems()[sender.get()])


		def btnSwitchLeftRightCallback(self, sender):
			if sender.get() == 0:
				self.direction = 'L'
			elif sender.get() == 1:
				self.direction = 'R'

			self.hideGroupedCallback(self.w.chbHideGrouped)
			self.w.groupsView.clear()
			self.w.groupsView.buildView(self.direction)
			self.w.cbGroupsList.setItems(self.w.groupsView.groupsList)


		def createGroup(self, font, glist):
			if len(glist) != 0:
				keyGlyph = glist[0]
				mask1 = ID_KERNING_GROUP.replace('.kern', '') + ID_GROUP_DIRECTION_POSITION_LEFT
				mask2 = ID_KERNING_GROUP.replace('.kern', '') + ID_GROUP_DIRECTION_POSITION_RIGHT
				if self.direction == 'L':
					groupname = '%s%s' % (mask1, keyGlyph)
				elif self.direction == 'R':
					groupname = '%s%s' % (mask2, keyGlyph)
				else: return
				# groupname = '%s_%s_%s' % (self.groupPrefix, self.direction, keyGlyph)
				# if not font.groups.has_key(groupname):
				# 	font.groups[groupname] = []
				# 	for gname in glist:
				# 		font.groups[groupname].append(gname)
				addGlyphsToGroup(self.font,groupname,glist)
				self.refresh(groupname)
				self.w.groupsView.scrollToGroup(groupname)
				self.w.groupsView.selectedGroup(groupname)


		def createGroupsByList(self, font, glist):
			for glyphname in glist:
				self.createGroup(font, [glyphname])


		def refreshCallback(self, sender):
			self.w.groupsView.clear()
			self.w.groupsView.buildView(self.direction)
			self.hideGroupedCallback(self.w.chbHideGrouped)
			self.w.cbGroupsList.setItems(self.w.groupsView.groupsList)

		def groupsChanged(self, groupname):
			self.w.groupsView.groupPrefix = self.groupPrefix
			self.w.groupsView.currentGroupName = groupname
			self.w.groupsView.updateGroupView(groupname)
			self.hideGroupedCallback(self.w.chbHideGrouped)


		def refresh(self, sender):
			self.w.groupsView.groupPrefix = self.groupPrefix
			self.w.groupsView.currentGroupName = sender
			self.w.groupsView.refresh()
			self.hideGroupedCallback(self.w.chbHideGrouped)
			self.w.cbGroupsList.setItems(self.w.groupsView.groupsList)


		def makeGroup(self, sender):
			glist = self.w.fontView.getSelectedGlyphs()
			self.createGroup(self.font, glist)


		def makeGroups(self, sender):
			glist = self.w.fontView.getSelectedGlyphs()
			self.createGroupsByList(self.font, glist)

		def deleteGroup(self, sender):
			self.w.groupsView.deleteGroupViewByName(self.w.groupsView.currentGroupName)
			self.w.cbGroupsList.setItems(self.w.groupsView.groupsList)
			self.w.cbGroupsList.setItem(getDisplayNameGroup(self.w.groupsView.currentGroupName))

	# fix layer color for GlyphCollectionView
	# CurrentFont().getLayer('foreground').color = (0, 0, 0, 1)

	MyW()
