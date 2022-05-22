# -*- coding: utf-8 -*-

import sys
from vanilla import *
from mojo.UI import *
from defconAppKit.windows.baseWindow import BaseWindowController
# from AppKit import *
from mojo.extensions import *
import importlib
import tdKernToolEssentials
importlib.reload(tdKernToolEssentials)
from tdKernToolEssentials import *

class KernPreferences(BaseWindowController):
	def __init__(self):

		self.w = FloatingWindow((430, 200), title = 'Kern Preferences')

		ID_KERNING_GROUP = getExtensionDefault(PREFKEY_GroupName, fallback = 'public.kern')
		ID_GROUP_DIRECTION_POSITION_LEFT = getExtensionDefault(PREFKEY_LeftID, fallback = '.kern1.')
		ID_GROUP_DIRECTION_POSITION_RIGHT = getExtensionDefault(PREFKEY_RightID, fallback = '.kern2.')
		KERNTOOL_UI_DARKMODE = getExtensionDefault(PREFKEY_DarkMode, fallback = False)
		KERNTOOL_UI_DARKMODE_WARMBACKGROUND = getExtensionDefault(PREFKEY_DarkModeWarmBackground, fallback = False)

		self.w.lblMMKname = TextBox((30,10,130,21),'Group Name ID')
		self.w.editMMKname = EditText((150,10,130,21),text = ID_KERNING_GROUP)
		self.w.lblLeftID = TextBox((30, 40, 100, 21), 'Left ID')
		self.w.editLeftId = EditText((150, 40, 130, 21), text = ID_GROUP_DIRECTION_POSITION_LEFT)
		self.w.lblRightID = TextBox((30, 70, 100, 21), 'Right ID')
		self.w.editRightId = EditText((150, 70, 130, 21), text = ID_GROUP_DIRECTION_POSITION_RIGHT)

		self.w.chkDarkMode = CheckBox((150,140,230,21), 'DarkMode', value = KERNTOOL_UI_DARKMODE)
		self.w.chkWarmBackground = CheckBox((150,160,230,21), 'WarmGrey Background', value = KERNTOOL_UI_DARKMODE_WARMBACKGROUND)

		self.w.btnApply = Button((320, 40, -20, 20), "Apply", callback=self.btnApplyCallback)

		self.w.open()

	def btnApplyCallback(self, sender):
		setExtensionDefault(PREFKEY_GroupName, self.w.editMMKname.get())
		setExtensionDefault(PREFKEY_LeftID, self.w.editLeftId.get())
		setExtensionDefault(PREFKEY_RightID, self.w.editRightId.get())
		setExtensionDefault(PREFKEY_DarkMode,self.w.chkDarkMode.get())
		setExtensionDefault(PREFKEY_DarkModeWarmBackground, self.w.chkWarmBackground.get())
		self.w.close()

KernPreferences()


