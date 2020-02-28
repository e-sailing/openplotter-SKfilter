#!/usr/bin/env python3

# This file is part of Openplotter.
# Copyright (C) 2019 by sailoog <https://github.com/sailoog/openplotter>
#                     e-sailing <https://github.com/e-sailing/openplotter>
# Openplotter is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# any later version.
# Openplotter is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Openplotter. If not, see <http://www.gnu.org/licenses/>.

import wx, os, webbrowser, subprocess, socket, pyudev, re, ujson, time, configparser
import wx.richtext as rt

from openplotterSettings import conf
from openplotterSettings import language
from openplotterSettings import platform
if os.path.dirname(os.path.abspath(__file__))[0:4] == '/usr':
	from openplotterSKfilter import nodes_SK_subflow
	from .version import version
else:
	import nodes_SK_subflow
	import version

class SKfilterFrame(wx.Frame):
	def __init__(self):
		self.conf = conf.Conf()
		self.conf_folder = self.conf.conf_folder
		self.home = self.conf_folder
		self.home = os.path.expanduser("~")
		
		self.SK = False
		self.home = os.path.expanduser("~")
		self.setting_file = self.home+'/.signalk/red/settings.json'
		if os.path.exists(self.setting_file):
			self.SK = True			
		
		self.platform = platform.Platform()
		self.currentdir = os.path.dirname(os.path.abspath(__file__))
		self.currentLanguage = self.conf.get('GENERAL', 'lang')
		self.language = language.Language(self.currentdir,'openplotter-SKfilter',self.currentLanguage)

		if os.path.dirname(os.path.abspath(__file__))[0:4] == '/usr': 
			v = version
		else: v = version.version
		wx.Frame.__init__(self, None, title=_('Signal K Filter'+' '+v), size=(800,444))
		self.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
		icon = wx.Icon(self.currentdir+"/data/openplotter-SKfilter-24.png", wx.BITMAP_TYPE_PNG)
		self.SetIcon(icon)
		self.CreateStatusBar()
		font_statusBar = self.GetStatusBar().GetFont()
		font_statusBar.SetWeight(wx.BOLD)
		self.GetStatusBar().SetFont(font_statusBar)

		self.toolbar1 = wx.ToolBar(self, style=wx.TB_TEXT)
		toolHelp = self.toolbar1.AddTool(101, _('Help'), wx.Bitmap(self.currentdir+"/data/help.png"))
		self.Bind(wx.EVT_TOOL, self.OnToolHelp, toolHelp)
		if not self.platform.isInstalled('openplotter-doc'): self.toolbar1.EnableTool(101,False)
		toolSettings = self.toolbar1.AddTool(102, _('Settings'), wx.Bitmap(self.currentdir+"/data/settings.png"))
		self.Bind(wx.EVT_TOOL, self.OnToolSettings, toolSettings)
		self.toolbar1.AddSeparator()
		diagnosticSK = self.toolbar1.AddTool(103, _('SK Diagnostic'), wx.Bitmap(self.currentdir+"/data/diagnosticSKinput-24.png"))
		self.Bind(wx.EVT_TOOL, self.OnDiagnosticSK, diagnosticSK)
		self.toolbar1.AddSeparator()
		SKrestart = self.toolbar1.AddTool(104, _('Restart Signal K'), wx.Bitmap(self.currentdir+"/data/sk.png"))
		self.Bind(wx.EVT_TOOL, self.on_restart_SK, SKrestart)
		self.toolbar1.AddSeparator()
		skNodeRed = self.toolbar1.AddTool(105, _('SK NodeRed'), wx.Bitmap(self.currentdir+"/data/sk.png"))
		self.Bind(wx.EVT_TOOL, self.OnSkNodeRed, skNodeRed)

		self.notebook = wx.Notebook(self)
		self.notebook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.onTabChange)
		self.p_SKfilter = wx.Panel(self.notebook)
		self.p_SKprefer = wx.Panel(self.notebook)
		self.connections = wx.Panel(self.notebook)
		self.output = wx.Panel(self.notebook)
		self.notebook.AddPage(self.p_SKfilter, _('Filter'))
		self.notebook.AddPage(self.p_SKprefer, _('Priority'))
		self.il = wx.ImageList(24, 24)
		img0 = self.il.Add(wx.Bitmap(self.currentdir+"/data/openplotter-SKfilter-24.png", wx.BITMAP_TYPE_PNG))
		self.notebook.AssignImageList(self.il)
		self.notebook.SetPageImage(0, img0)
		self.notebook.SetPageImage(1, img0)

		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox.Add(self.toolbar1, 0, wx.EXPAND)
		vbox.Add(self.notebook, 1, wx.EXPAND)
		self.SetSizer(vbox)

		self.pageSKfilter()
		self.read_filter()
		self.pageSKprefer()
		self.read_prefer()
		
		self.Centre(True) 

	def ShowStatusBar(self, w_msg, colour):
		self.GetStatusBar().SetForegroundColour(colour)
		self.SetStatusText(w_msg)

	def ShowStatusBarRED(self, w_msg):
		self.ShowStatusBar(w_msg, (130,0,0))

	def ShowStatusBarGREEN(self, w_msg):
		self.ShowStatusBar(w_msg, (0,130,0))

	def ShowStatusBarBLACK(self, w_msg):
		self.ShowStatusBar(w_msg, wx.BLACK) 

	def ShowStatusBarYELLOW(self, w_msg):
		self.ShowStatusBar(w_msg,(255,140,0))

	def onTabChange(self, event):
		try:
			self.SetStatusText('')
		except:pass

	def onTabChange(self, event):
		try:
			self.SetStatusText('')
		except:
			pass

	# create your page in the manuals and add the link here
	def OnToolHelp(self, event): 
		url = "/usr/share/openplotter-doc/template/SKfilter_app.html"
		webbrowser.open(url, new=2)

	def OnToolSettings(self, event): 
		subprocess.call(['pkill', '-f', 'openplotter-settings'])
		subprocess.Popen('openplotter-settings')
		
	def OnDiagnosticSK(self, event): 
		subprocess.call(['pkill', '-f', 'diagnostic-SKinput'])
		subprocess.Popen(['diagnostic-SKinput'])

	def OnToolSend(self,e):
		self.notebook.ChangeSelection(0)
		if self.toolbar1.GetToolState(103): self.myoption.SetLabel('1')
		else: self.myoption.SetLabel('0')

	def OnSkNodeRed(self,e):
		url = self.platform.http+'localhost:'+self.platform.skPort+'/plugins/signalk-node-red/redAdmin'
		webbrowser.open(url, new=2)	

	def pageSKfilter(self):
		self.available_operators = ['eq', 'neq', 'lt', 'lte', 'gt', 'gte','btwn', 'cont', 'true', 'false', 'null', 'nnull', 'empty', 'nempty']
		self.available_conditions = ['=', '!=', '<', '<=', '>', '>=', _('is between'), _('contains'), _('is true'), _('is false'), _('is null'), _('is not null'), _('is empty'), _('is not empty')]		

		self.available_source = [_('label'),_('type'),_('pgn'),_('src'),_('sentence'),_('talker')]
		self.available_source_nr = ['label','type','pgn','src','sentence','talker']

		self.SetBackgroundColour(wx.Colour(230,230,230,255))
		
		self.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
		
		self.icon = wx.Icon(self.currentdir+"/data/openplotter-SKfilter-24.png", wx.BITMAP_TYPE_PNG)
		self.SetIcon(self.icon)

		self.list_filter = wx.ListCtrl(self.p_SKfilter, -1, style=wx.LC_REPORT | wx.SIMPLE_BORDER)
		self.list_filter.InsertColumn(0, _('Signal K key'), width=240)
		self.list_filter.InsertColumn(1, _('Source Type'), width=120)
		self.list_filter.InsertColumn(2, _('Condition'), width=70)
		self.list_filter.InsertColumn(3, _('Value'), width=90)
		self.list_filter.InsertColumn(4, _('Value2'), width=60)

		self.list_filter.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onSelected)
		self.list_filter.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnEditButton)

		self.toolbar2 = wx.ToolBar(self.p_SKfilter, style=wx.TB_TEXT | wx.TB_VERTICAL)
		self.addButton = self.toolbar2.AddTool(201, _('Add'), wx.Bitmap(self.currentdir+"/data/openplotter-SKfilter-24.png"))
		self.Bind(wx.EVT_TOOL, self.OnAddButton, self.addButton)
		self.editButton = self.toolbar2.AddTool(202, _('Edit'), wx.Bitmap(self.currentdir+"/data/edit.png"))
		self.Bind(wx.EVT_TOOL, self.OnEditButton, self.editButton)
		self.removeButton = self.toolbar2.AddTool(204, _('Remove'), wx.Bitmap(self.currentdir+"/data/cancel.png"))
		self.Bind(wx.EVT_TOOL, self.OnRemoveButton, self.removeButton)

		sizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer.Add(self.list_filter, 1, wx.EXPAND, 0)
		sizer.Add(self.toolbar2, 0)

		self.p_SKfilter.SetSizer(sizer)
		
		font_statusBar = self.GetStatusBar().GetFont()
		font_statusBar.SetWeight(wx.BOLD)
		self.GetStatusBar().SetFont(font_statusBar)
		self.GetStatusBar().SetForegroundColour(wx.BLACK)
		self.toolbar2.EnableTool(202,False)
		self.toolbar2.EnableTool(204,False)		

	def read_filter(self):
		self.nodes = nodes_SK_subflow.Nodes(self)
		self.nodes.get_flow()
		self.on_print_filter()

	def on_print_filter(self):
		self.list_filter.DeleteAllItems()
		for nodesi in self.nodes.OPnodes:
			self.list_filter.Append([nodesi[2], nodesi[3], nodesi[4], nodesi[5], nodesi[7]])

	def onSelected(self, e):
		self.selected_filter = self.list_filter.GetFirstSelected()
		i = e.GetIndex()
		valid = e and i >= 0
		if not valid: return
		#self.onDeselected()
		self.selected = i
		if self.list_filter.GetItemBackgroundColour(i) != (200,200,200):
			self.toolbar2.EnableTool(202,True)
			self.toolbar2.EnableTool(204,True)

	def OnEditButton(self, e):
		if self.selected_filter == -1: return
		self.edit_add_filter(self.selected_filter)

	def OnAddButton(self, e):
		self.edit_add_filter(-1)

	def edit_add_filter(self, line):
		dlg = nodes_SK_subflow.SetupFilterSK(self,line)
		res = dlg.ShowModal()
		if res == wx.OK:
			self.nodes.write_flow()
			self.on_print_filter()
		dlg.Destroy()

	def OnRemoveButton(self, e):
		self.nodes.OPnodes.remove(self.nodes.OPnodes[self.selected_filter])
		self.nodes.write_flow()
		self.on_print_filter()
		self.toolbar2.EnableTool(202,False)
		self.toolbar2.EnableTool(204,False)
		
	def pageSKprefer(self):
		self.available_operators = ['eq', 'neq', 'lt', 'lte', 'gt', 'gte','btwn', 'cont', 'true', 'false', 'null', 'nnull', 'empty', 'nempty']
		self.available_conditions = ['=', '!=', '<', '<=', '>', '>=', _('is between'), _('contains'), _('is true'), ('is false'), _('is null'), _('is not null'), _('is empty'), _('is not empty')]		

		self.available_source = [_('label'),_('type'),_('pgn'),_('src'),_('sentence'),_('talker')]
		self.available_source_nr = ['label','type','pgn','src','sentence','talker']

		self.SetBackgroundColour(wx.Colour(230,230,230,255))
		
		self.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
		
		self.icon = wx.Icon(self.currentdir+"/data/openplotter-SKfilter.png", wx.BITMAP_TYPE_PNG)
		self.SetIcon(self.icon)

		self.list_prefer = wx.ListCtrl(self.p_SKprefer, -1, style=wx.LC_REPORT | wx.SIMPLE_BORDER)
		self.list_prefer.InsertColumn(0, _('Signal K key'), width=240)
		self.list_prefer.InsertColumn(1, _('Source Type'), width=120)
		self.list_prefer.InsertColumn(2, _('Value'), width=70)
		self.list_prefer.InsertColumn(3, _('max Timeout'), width=100)

		self.list_prefer.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onSelected2)
		self.list_prefer.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnEditButton2)

		self.toolbar3 = wx.ToolBar(self.p_SKprefer, style=wx.TB_TEXT | wx.TB_VERTICAL)
		self.addButton2 = self.toolbar3.AddTool(301, _('Add'), wx.Bitmap(self.currentdir+"/data/openplotter-SKfilter-24.png"))
		self.Bind(wx.EVT_TOOL, self.OnAddButton2, self.addButton2)
		self.editButton2 = self.toolbar3.AddTool(302, _('Edit'), wx.Bitmap(self.currentdir+"/data/edit.png"))
		self.Bind(wx.EVT_TOOL, self.OnEditButton2, self.editButton2)
		self.removeButton2 = self.toolbar3.AddTool(304, _('Remove'), wx.Bitmap(self.currentdir+"/data/cancel.png"))
		self.Bind(wx.EVT_TOOL, self.OnRemoveButton2, self.removeButton2)

		sizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer.Add(self.list_prefer, 1, wx.EXPAND, 0)
		sizer.Add(self.toolbar3, 0)

		self.p_SKprefer.SetSizer(sizer)
		
		font_statusBar = self.GetStatusBar().GetFont()
		font_statusBar.SetWeight(wx.BOLD)
		self.GetStatusBar().SetFont(font_statusBar)
		self.GetStatusBar().SetForegroundColour(wx.BLACK)
		self.toolbar3.EnableTool(302,False)
		self.toolbar3.EnableTool(304,False)		

	def read_prefer(self):
		self.nodes = nodes_SK_subflow.Nodes(self)
		self.nodes.get_flow()
		self.on_print_prefer()

	def on_print_prefer(self):
		self.list_prefer.DeleteAllItems()
		for nodesi in self.nodes.PPnodes:
			self.list_prefer.Append([nodesi[1], nodesi[4], nodesi[3], nodesi[2]])

	def onSelected2(self, e):
		self.selected_prefer = self.list_prefer.GetFirstSelected()
		i = e.GetIndex()
		valid = e and i >= 0
		if not valid: return
		#self.onDeselected()
		self.selected = i
		if self.list_prefer.GetItemBackgroundColour(i) != (200,200,200):
			self.toolbar3.EnableTool(302,True)
			self.toolbar3.EnableTool(304,True)
		
	def OnEditButton2(self, e):
		if self.selected_prefer == -1: return
		self.edit_add_prefer(self.selected_prefer)

	def OnAddButton2(self, e):
		self.edit_add_prefer(-1)

	def edit_add_prefer(self, line):
		dlg = nodes_SK_subflow.SetupPreferSK(self,line)
		res = dlg.ShowModal()
		if res == wx.OK:
			self.nodes.write_flow()
			self.on_print_prefer()
		dlg.Destroy()

	def OnRemoveButton2(self, e):
		self.nodes.PPnodes.remove(self.nodes.PPnodes[self.selected_prefer])
		self.nodes.write_flow()
		self.on_print_prefer()
		self.toolbar3.EnableTool(302,False)
		self.toolbar3.EnableTool(304,False)		

	def on_help_prefer(self, e):
		url = "/usr/share/openplotter-doc/tools/prefer_signalk_inputs.html"
		webbrowser.open(url, new=2)

	def on_restart_SK(self, e):
		msg = _('Restarting Signal K server... ')
		seconds = 12
		subprocess.call([self.platform.admin, 'python3', self.currentdir+'/service.py', 'restart'])
		for i in range(seconds, 0, -1):
			self.ShowStatusBarYELLOW(msg+str(i))
			time.sleep(1)
		self.ShowStatusBarGREEN(_('Signal K server restarted'))

def main():
	try:
		platform2 = platform.Platform()
		if not platform2.postInstall(version,'SKfilter'):
			subprocess.Popen(['openplotterPostInstall', platform2.admin+' SKfilterPostInstall'])
			return
	except: pass

	app = wx.App()
	SKfilterFrame().Show()
	time.sleep(1)
	app.MainLoop()

if __name__ == '__main__':
	main()
