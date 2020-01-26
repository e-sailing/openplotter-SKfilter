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

import ujson, uuid, wx, re, time, webbrowser, datetime, os, socket
if os.path.dirname(os.path.abspath(__file__))[0:4] == '/usr':
	from openplotterSKfilter import select_key
else:
	import select_key

class Nodes:
	def __init__(self,parent):
		self.available_conditions = parent.available_conditions
		self.available_operators = parent.available_operators
		
		home = parent.home
		
		self.setting_file = home+'/.signalk/plugin-config-data/signalk-node-red.json'
		try:
			with open(self.setting_file) as data_file:
				data = ujson.load(data_file)
				flow_set=data['configuration']['flowFile']
		except:
			print("self.setting_file")
			
		if flow_set != '':
			flow_name=data['configuration']['flowFile']
		else:
			flow_name='flows_'+socket.gethostname()+'.json'
		
		self.flows_file = home+'/.signalk/red/'+flow_name
		print(self.flows_file)
	
	def get_subflow_data(self):
		node_title = '''
			[
				{
					"id": "openplot.filter",
					"type": "tab",
					"label": "OpenPlotter Filter",
					"disabled": false,
					"info": "Please do not edit this flow. Use the OpenPlotter interface to make changes on it."
				},
				{
					"id": "openplot.comme",
					"type": "comment",
					"z": "openplot.filter",
					"name": "Please do not edit this flow. Use the OpenPlotter interface to make changes on it.",
					"info": "",
					"x": 310,
					"y": 20,
					"wires": []
				}
			]'''
		return ujson.loads(node_title)

	def search_flow(self,search):
		for i in self.data:
			if i['id'] == search:
				return i

	def get_flow(self):
		#this read json file and get all infos from OPxxx
		self.data = self.read_flow()
		self.OPnodes = []
		self.PPnodes = []
		
		for i in self.data:
			if i['id'][0:2] == 'OP' and i['id'][6:13] == 'subflow':
				list = []
				j = self.search_flow(i['id'][0:5]+'.a.subflow')
				k = self.search_flow(i['id'][0:5]+'.b.subflow')
				list.append(i['id'][0:5])
				list.append(j['context'])
				list.append(j['path'])
				list.append(k['property'])
				list.append(k['rules'][0]['t'])

				if 'vt' in k['rules'][0]:
					list.append(k['rules'][0]['v'])
					list.append(k['rules'][0]['vt'])
				else:
					list.append('')
					list.append('')					
					
				if 'v2' in k['rules'][0]:
					list.append(k['rules'][0]['v2'])
					list.append(k['rules'][0]['v2t'])
				else:
					list.append('')
					list.append('')
				self.OPnodes.append(list)
				
		for i in self.data:
			if i['id'][0:2] == 'PP' and i['id'][6:12] == 'prefer':
				list = []
				j = self.search_flow(i['id'][0:5]+'.a.prefer')
				k = self.search_flow(i['id'][0:5]+'.b.prefer')
				list.append(i['id'][0:5])
				list.append(j['path'])
				
				l=k['func'].split('\n')
				#const timeout = OPtime
				m = l[1].split('=')
				if len(m)==2: 	list.append(m[1])
				else: 			list.append('')
					
				#const prefered = 'OPprefered'
				m = l[2].split("'")
				if len(m)==3: 	list.append(m[1])
				else: 			list.append('')

				#erg = msg.source.OPproperty
				m = l[9].split(".")
				if len(m)==3: 	list.append(m[2])
				else: 			list.append('')
				self.PPnodes.append(list)
	
	def read_flow(self):
		try:
			with open(self.flows_file) as data_file:
				data = ujson.load(data_file)
			return data
		except:
			print("ERROR reading flows file")
			return []
			
	def write_flow(self):	
		node_filter = '''
			[
				{
					"id": "OPxxx.subflow",
					"type": "subflow",
					"name": "OPxxx",
					"info": "",
					"in": [],
					"out": []
				},
				{
					"id": "OPxxx.0.subflow",
					"type": "subflow:OPxxx.subflow",
					"z": "openplot.filter",
					"x": 90,
					"y": OPy,
					"wires": []
				},
				{
					"id": "OPxxx.a.subflow",
					"type": "signalk-input-handler",
					"z": "OPxxx.subflow",
					"name": "OPxxx.a.subflow",
					"context": "OPcontext",
					"path": "OPpath",
					"source": "",
					"x": 140,
					"y": 60,
					"wires": [
						[
							"OPxxx.b.subflow"
						]
					]
				},
				{
					"id": "OPxxx.b.subflow",
					"type": "switch",
					"z": "OPxxx.subflow",
					"name": "OPxxx.b.subflow",
					"property": "OPproperty",
					"propertyType": "msg",
					"rules": [
							OPrules
					],
					"checkall": "true",
					"repair": false,
					"outputs": 1,
					"x": 360,
					"y": 60,
					"wires": [
						[
							"OPxxx.c.subflow"
						]
					]
				},
				{
					"id": "OPxxx.c.subflow",
					"type": "signalk-input-handler-next",
					"z": "OPxxx.subflow",
					"name": "OPxxx.c.subflow",
					"x": 580,
					"y": 60,
					"wires": []
				}
			]'''

		node_prefer = '''
			[
				{
					"id": "PPxxx.prefer",
					"type": "subflow",
					"name": "PPxxx",
					"info": "",
					"category": "",
					"in": [],
					"out": []
				},
				{
					"id": "PPxxx.0.prefer",
					"type": "subflow:PPxxx.prefer",
					"z": "openplot.filter",
					"x": 90,
					"y": OPy,
					"wires": []
				},
				{
					"id": "PPxxx.a.prefer",
					"type": "signalk-input-handler",
					"z": "PPxxx.prefer",
					"name": "PPxxx.a.prefer",
					"context": "vessels.self",
					"path": "OPpath",
					"source": "",
					"x": 110,
					"y": 40,
					"wires": [
						[
							"PPxxx.b.prefer"
						]
					]
				},
				{
					"id": "PPxxx.b.prefer",
					"type": "function",
					"z": "PPxxx.prefer",
					"name": "PPxxx.b.prefer",
					"func": "OPfunc",
					"outputs": 1,
					"noerr": 0,
					"x": 380,
					"y": 40,
					"wires": [
						[
							"PPxxx.c.prefer"
						]
					]
				},
				{
					"id": "PPxxx.c.prefer",
					"type": "signalk-input-handler-next",
					"z": "PPxxx.prefer",
					"name": "",
					"x": 660,
					"y": 40,
					"wires": []
				}
			]'''

		OPfunc = "\nconst timeout = OPtime\nconst prefered = 'OPprefered'\nlet lastSeen = context.get('lastSeen')\n\nvar erg = '';\nif (msg.hasOwnProperty(\"source\")) {\n    if (msg.source !== undefined) {\n        if (msg.source.hasOwnProperty(\"OPproperty\")) {\n            erg = msg.source.OPproperty\n        }\n    }\n}\n//node.warn(\"erg \"+erg)\n\nif ( erg === prefered )\n{\n    node.send(msg)\n    context.set('lastSeen', Date.now())\n    //node.error('go it')\n} else if ( !lastSeen ) {\n    node.send(msg)\n    //node.error('no last')\n} else if ( Date.now() - lastSeen > (timeout *1000)) {\n    node.send(msg)\n    //node.error('timeout')\n}\n\n"

		newdata = self.get_subflow_data()
		
		for i in self.data:
			if not (i['id'][0:2] in ['OP','PP'] or i['id'][0:8] == 'openplot') :
				newdata.append(i)
		#OP
		ii = 0
		for i in self.OPnodes:
			ii += 1
			x = node_filter.replace("OPxxx", i[0])
			x = x.replace("OPcontext", i[1])
			x = x.replace("OPpath", i[2])
			x = x.replace("OPproperty", i[3])
			x = x.replace("OPy", str(20+ii*40))
			
			s = '{"t": "'+i[4]+'"'
			if i[4] in ['eq', 'neq', 'lt', 'lte', 'gt', 'gte','btwn', 'cont']:	
				s += ', "v": "'+i[5]+'", "vt": "'+i[6]+'"'
				if i[4] == 'btwn':
					s += ', "v2": "'+i[7]+'", "v2t": "'+i[8]+'"'
			s += '}'
			
			x = x.replace("OPrules", s)
			x = ujson.loads(x)
			
			for j in x:
				newdata.append(j)
		#PP
		for i in self.PPnodes:
			ii += 1
			x = node_prefer.replace("PPxxx", i[0])
			x = x.replace("OPpath", i[1])
			x = x.replace("OPy", str(20+ii*40))
			
			y = OPfunc.replace("OPtime", i[2])
			y = y.replace("OPprefered", i[3])
			y = y.replace("OPproperty", i[4])
					
			x = ujson.loads(x)
			for k in x:
				if k['id'][6:7] == 'b':
					k['func'] = y			
			
			for j in x:
				newdata.append(j)
	
		try:
			data = ujson.dumps(newdata, indent=4)
			#print(data)
			with open(self.flows_file, "w") as outfile:
				outfile.write(data)
		except: print("ERROR writing flows file")


class SetupFilterSK(wx.Dialog):
	def __init__(self, parent, line):
		self.currentpath = parent.currentdir
		self.parent = parent
		self.old = []

		self.available_operators = parent.available_operators
		self.available_conditions = parent.available_conditions
		
		self.available_source = parent.available_source
		self.available_source_nr = parent.available_source_nr
	
		help_bmp = wx.Bitmap(parent.currentdir+"/data/help.png")

		if line == -1: title = _('Add Signal K filter')
		else: title = _('Edit Signal K filter')

		wx.Dialog.__init__(self, None, title = title, size=(400, 370))
		self.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))

		panel = wx.Panel(self)
		panel.SetBackgroundColour(wx.Colour(230,230,230,255))

		vessellabel = wx.StaticText(panel, label=_('Vessel'))
		self.vessel = wx.TextCtrl(panel, size=(290,-1))

		vessel = wx.BoxSizer(wx.HORIZONTAL)
		vessel.Add(vessellabel, 1, wx.RIGHT | wx.ALL | wx.EXPAND, 6)
		vessel.Add(self.vessel, 0, wx.RIGHT, 10)

		skkeylabel = wx.StaticText(panel, label=_('Signal K key'))
		self.skkey = wx.TextCtrl(panel, size=(290,-1))
		if line == -1: edit_skkey = wx.Button(panel, label=_('Add'))
		else: edit_skkey = wx.Button(panel, label=_('Edit'))
		#showlist_multipleSK = wx.Button(panel, label=_('list SK with multiple source'))
		edit_skkey.Bind(wx.EVT_BUTTON, self.onEditSkkey)
		
		skkey = wx.BoxSizer(wx.HORIZONTAL)
		skkey.Add(skkeylabel, 1, wx.RIGHT | wx.ALL | wx.EXPAND, 6)
		skkey.Add(self.skkey, 0, wx.RIGHT, 10)
		
		editskkey = wx.BoxSizer(wx.HORIZONTAL)
		editskkey.AddSpacer(10)
		#editskkey.Add(showlist_multipleSK, 0, wx.RIGHT, 10)		
		editskkey.AddStretchSpacer(1)
		editskkey.Add(edit_skkey, 0, wx.RIGHT, 10)		

		sourcelabel = wx.StaticText(panel, label=_('filter on Source'))
		self.source_select = wx.Choice(panel, choices=self.available_source, style=wx.CB_READONLY)

		source = wx.BoxSizer(wx.HORIZONTAL)
		source.Add(sourcelabel, 0, wx.TOP | wx.BOTTOM, 6)
		source.Add(self.source_select, 0, wx.LEFT, 5)

		operatorlabel = wx.StaticText(panel, label=_('Operator'))
		self.available_operators_select = wx.Choice(panel, choices=self.available_conditions, style=wx.CB_READONLY)
		self.available_operators_select.Bind(wx.EVT_CHOICE, self.on_available_operators_select)

		typeoperator = wx.BoxSizer(wx.HORIZONTAL)
		typeoperator.Add(operatorlabel, 0, wx.TOP | wx.BOTTOM, 6)
		typeoperator.Add(self.available_operators_select, 0, wx.LEFT, 5)

		type_list = [_('String'), _('Number')]
		self.type_list = ['str', 'num']

		value1label = wx.StaticText(panel, label=_('Value'))
		self.value1 = wx.TextCtrl(panel)

		value1 = wx.BoxSizer(wx.HORIZONTAL)
		value1.Add(value1label, 0, wx.TOP | wx.BOTTOM, 9)
		value1.AddSpacer(5)
		value1.Add(self.value1, 1, wx.TOP | wx.BOTTOM, 3)

		value2label = wx.StaticText(panel, label=_('Value'))
		self.value2 = wx.TextCtrl(panel)
		
		value2 = wx.BoxSizer(wx.HORIZONTAL)
		value2.Add(value2label, 0, wx.TOP | wx.BOTTOM, 9)
		value2.AddSpacer(5)
		value2.Add(self.value2, 1, wx.TOP | wx.BOTTOM, 3)

		hline1 = wx.StaticLine(panel)
		help_button = wx.BitmapButton(panel, bitmap=help_bmp, size=(help_bmp.GetWidth()+40, help_bmp.GetHeight()+10))
		help_button.Bind(wx.EVT_BUTTON, self.on_help)
		cancelBtn = wx.Button(panel, wx.ID_CANCEL, label=_('Cancel'))
		okBtn = wx.Button(panel, wx.ID_OK, label=_('OK'))
		okBtn.Bind(wx.EVT_BUTTON, self.OnOk)

		hbox = wx.BoxSizer(wx.HORIZONTAL)
		hbox.Add(help_button, 0, wx.ALL, 10)
		hbox.AddStretchSpacer(1)
		hbox.Add(cancelBtn, 0, wx.ALL, 10)
		hbox.Add(okBtn, 0, wx.ALL, 10)
		
		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox.AddSpacer(10)
		vbox.Add(vessel, 0, wx.LEFT | wx.EXPAND, 5)
		vbox.Add(skkey, 0, wx.LEFT | wx.EXPAND, 5)
		vbox.AddSpacer(3)
		vbox.Add(editskkey, 0, wx.ALL | wx.EXPAND, 0)
		vbox.AddStretchSpacer(1)
		vbox.Add(source, 0, wx.ALL, 10)
		vbox.Add(typeoperator, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
		vbox.Add(value1, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)
		vbox.Add(value2, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)
		vbox.Add(hline1, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
		vbox.Add(hbox, 0, wx.ALL | wx.EXPAND, 0)

		panel.SetSizer(vbox)
		
		if line == -1:
			i = 0
			
			while True:
				i += 1
				found = False
				
				if i>9:
					OPc = 'OP0'+str(i)
				else:
					OPc = 'OP00'+str(i)
					
				for j in self.parent.nodes.OPnodes:				
					if j[0] == OPc: found = True
				
				if i>50 or not found: break
			self.parent.nodes.OPnodes.append([OPc,'vessels.self','','','','','','',''])
			self.old = self.parent.nodes.OPnodes[len(self.parent.nodes.OPnodes)-1]		
		else:
			self.old = self.parent.nodes.OPnodes[line]		
			
		self.vessel.SetValue(self.old[1].replace('vessels.',''))
		self.skkey.SetValue(self.old[2])
		try:
			self.source_select.SetSelection(self.available_source_nr.index(self.old[3].replace('source.','')))
			self.available_operators_select.SetSelection(self.available_operators.index(self.old[4]))
		except: pass
		self.value1.SetValue(self.old[5])
		self.value2.SetValue(self.old[7])
		
		self.operator = self.old[4]
		if self.operator == 'true' or self.operator == 'false' or self.operator == 'null' or self.operator == 'nnull' or self.operator == 'empty' or self.operator == 'nempty':
			self.type1.Disable()
			self.value1.Disable()
			
		if self.operator != 'btwn':			
			self.value2.Disable()			

	def on_help(self, e):
		url = "/usr/share/openplotter-doc/tools/filter_signalk_inputs.html"
		webbrowser.open(url, new=2)

	def onEditSkkey(self,e):
		oldkey = False
		if self.skkey.GetValue(): oldkey = self.skkey.GetValue()
		dlg = select_key.selectKey(oldkey,1)
		res = dlg.ShowModal()
		if res == wx.OK: 
			self.skkey.SetValue(dlg.selected_key)
			self.vessel.SetValue(dlg.selected_vessel)
		dlg.Destroy()

	def OnOk(self,e):
		skkey = self.skkey.GetValue()
		vessel = self.vessel.GetValue()
		source = ''
		if not skkey:
			wx.MessageBox(_('You have to provide a Signal K key.'), 'Info', wx.OK | wx.ICON_INFORMATION)
			return
		elif not vessel:
			wx.MessageBox(_('You have to provide a vessel ID.'), 'Info', wx.OK | wx.ICON_INFORMATION)
			return
		elif source and not re.match('^[.0-9a-zA-Z]+$', source):
			wx.MessageBox(_('Failed. Characters not allowed.'), 'Info', wx.OK | wx.ICON_INFORMATION)
			return
		elif self.source_select.GetSelection() == -1:	
			wx.MessageBox(_('You have to provide a filter.'), 'Info', wx.OK | wx.ICON_INFORMATION)
			return
		elif self.available_operators_select.GetSelection() == -1:	
			wx.MessageBox(_('You have to provide an operator '), 'Info', wx.OK | wx.ICON_INFORMATION)
			return
		
		self.old[1] = 'vessels.'+vessel
		self.old[2] = skkey
		self.old[3] = 'source.'+self.available_source[self.source_select.GetSelection()]
		self.old[4] = self.available_operators[self.available_operators_select.GetSelection()]

		if self.old[4] in ['eq', 'neq', 'lt', 'lte', 'gt', 'gte','btwn', 'cont']:	
			if not self.value1.GetValue():
				wx.MessageBox(_('You have to provide a values.'), 'Info', wx.OK | wx.ICON_INFORMATION)
				return

			self.old[5] = self.value1.GetValue()
			self.old[6] = 'str'
			if self.source_select.GetSelection() == self.available_source_nr.index('pgn'):
				self.old[6] = 'num'

		if self.old[4] == 'btwn':
			if not self.value2.GetValue():
				wx.MessageBox(_('You have to provide 2 values.'), 'Info', wx.OK | wx.ICON_INFORMATION)
				return

			self.old[7] = self.value2.GetValue()
			self.old[8] = 'str'
			if self.source_select.GetSelection() == self.available_source_nr.index('pgn'):
				self.old[8] = 'num'
		
		self.EndModal(wx.OK)

	def on_available_operators_select(self,e):
		self.operator = self.available_operators[self.available_operators_select.GetSelection()]
		
		self.value1.Enable()
		self.value2.Disable()
		if self.operator in ['true','false','null','nnull','empty','nempty']:
			self.value1.Disable()
		if self.operator == 'btwn':			
			self.value2.Enable()
			
			
class SetupPreferSK(wx.Dialog):
	def __init__(self, parent, line):
		self.currentpath = parent.currentdir
		self.parent = parent
		self.old = []
		
		self.available_source = parent.available_source
		self.available_source_nr = parent.available_source_nr
	
		help_bmp = wx.Bitmap(parent.currentdir+"/data/help.png")

		if line == -1: title = _('Add Signal K prefer')
		else: title = _('Edit Signal K prefer')

		wx.Dialog.__init__(self, None, title = title, size=(400, 370))
		self.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))

		panel = wx.Panel(self)
		panel.SetBackgroundColour(wx.Colour(230,230,230,255))

		skkeylabel = wx.StaticText(panel, label=_('Signal K key'))
		self.skkey = wx.TextCtrl(panel, size=(290,-1))
		if line == -1: edit_skkey = wx.Button(panel, label=_('Add'))
		else: edit_skkey = wx.Button(panel, label=_('Edit'))
		#showlist_multipleSK = wx.Button(panel, label=_('list SK with multiple source'))
		edit_skkey.Bind(wx.EVT_BUTTON, self.onEditSkkey)
		
		skkey = wx.BoxSizer(wx.HORIZONTAL)
		skkey.Add(skkeylabel, 1, wx.RIGHT | wx.ALL | wx.EXPAND, 6)
		skkey.Add(self.skkey, 0, wx.RIGHT, 10)
		
		editskkey = wx.BoxSizer(wx.HORIZONTAL)
		editskkey.AddSpacer(10)
		#editskkey.Add(showlist_multipleSK, 0, wx.RIGHT, 10)		
		editskkey.AddStretchSpacer(1)
		editskkey.Add(edit_skkey, 0, wx.RIGHT, 10)		

		sourcelabel = wx.StaticText(panel, label=_('filter on Source'))
		self.source_select = wx.Choice(panel, choices=self.available_source, style=wx.CB_READONLY)

		source = wx.BoxSizer(wx.HORIZONTAL)
		source.Add(sourcelabel, 0, wx.TOP | wx.BOTTOM, 6)
		source.Add(self.source_select, 0, wx.LEFT, 5)

		value1label = wx.StaticText(panel, label=_('Value'))
		self.value1 = wx.TextCtrl(panel)

		wtimelabel = wx.StaticText(panel, label=_('max timeout[s]'))
		self.wtime = wx.TextCtrl(panel)

		value1 = wx.BoxSizer(wx.HORIZONTAL)
		value1.Add(value1label, 0, wx.TOP | wx.BOTTOM, 9)
		value1.AddSpacer(5)
		value1.Add(self.value1, 1, wx.TOP | wx.BOTTOM, 3)

		wtime = wx.BoxSizer(wx.HORIZONTAL)
		wtime.Add(wtimelabel, 0, wx.TOP | wx.BOTTOM, 9)
		wtime.AddSpacer(5)
		wtime.Add(self.wtime, 1, wx.TOP | wx.BOTTOM, 3)

		hline1 = wx.StaticLine(panel)
		help_button = wx.BitmapButton(panel, bitmap=help_bmp, size=(help_bmp.GetWidth()+40, help_bmp.GetHeight()+10))
		help_button.Bind(wx.EVT_BUTTON, self.on_help)
		cancelBtn = wx.Button(panel, wx.ID_CANCEL, label=_('Cancel'))
		okBtn = wx.Button(panel, wx.ID_OK, label=_('OK'))
		okBtn.Bind(wx.EVT_BUTTON, self.OnOk)

		hbox = wx.BoxSizer(wx.HORIZONTAL)
		hbox.Add(help_button, 0, wx.ALL, 10)
		hbox.AddStretchSpacer(1)
		hbox.Add(cancelBtn, 0, wx.ALL, 10)
		hbox.Add(okBtn, 0, wx.ALL, 10)
		
		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox.AddSpacer(10)
		vbox.Add(skkey, 0, wx.LEFT | wx.EXPAND, 5)
		vbox.AddSpacer(3)
		vbox.Add(editskkey, 0, wx.ALL | wx.EXPAND, 0)
		vbox.AddStretchSpacer(1)
		vbox.Add(source, 0, wx.ALL, 10)
		vbox.Add(value1, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)
		vbox.Add(wtime, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)
		vbox.Add(hline1, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
		vbox.Add(hbox, 0, wx.ALL | wx.EXPAND, 0)

		panel.SetSizer(vbox)
		
		if line == -1:
			i = 0
			
			while True:
				i += 1
				found = False
				
				if i>9:
					OPc = 'PP0'+str(i)
				else:
					OPc = 'PP00'+str(i)
					
				for j in self.parent.nodes.PPnodes:				
					if j[0] == OPc: found = True
				
				if i>50 or not found: break
			self.parent.nodes.PPnodes.append([OPc,'','5','',''])
			self.old = self.parent.nodes.PPnodes[len(self.parent.nodes.PPnodes)-1]		
		else:
			self.old = self.parent.nodes.PPnodes[line]		
			
		self.skkey.SetValue(self.old[1])
		self.wtime.SetValue(self.old[2])
		self.value1.SetValue(self.old[3])
		try:
			self.source_select.SetSelection(self.available_source_nr.index(self.old[4]))
		except: pass
		
	def on_help(self, e):
		url = "/usr/share/openplotter-doc/tools/prefered_signalk_inputs.html"
		webbrowser.open(url, new=2)

	def onEditSkkey(self,e):
		oldkey = False
		if self.skkey.GetValue(): oldkey = self.skkey.GetValue()
		dlg = select_key.selectKey(oldkey,1)
		res = dlg.ShowModal()
		if res == wx.OK: 
			self.skkey.SetValue(dlg.selected_key)
		dlg.Destroy()

	def OnOk(self,e):
		skkey = self.skkey.GetValue()
		source = ''
		if not skkey:
			wx.MessageBox(_('You have to provide a Signal K key.'), 'Info', wx.OK | wx.ICON_INFORMATION)
			return
		elif source and not re.match('^[.0-9a-zA-Z]+$', source):
			wx.MessageBox(_('Failed. Characters not allowed.'), 'Info', wx.OK | wx.ICON_INFORMATION)
			return
		elif self.source_select.GetSelection() == -1:	
			wx.MessageBox(_('You have to provide a filter.'), 'Info', wx.OK | wx.ICON_INFORMATION)
			return
		
		self.old[1] = skkey
		self.old[2] = self.wtime.GetValue()
		self.old[3] = self.value1.GetValue()
		self.old[4] = self.available_source[self.source_select.GetSelection()]

		self.EndModal(wx.OK)
