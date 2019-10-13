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

import wx, os, websocket, subprocess, ujson, time, threading, logging

from openplotterSettings import conf
from openplotterSettings import language

from getkeys import GetKeys
from show_keys import showKeys

class MyFrame(wx.Frame):
	def __init__(self):
		self.SK_unit = ''
		self.SK_description = ''
		self.SK_unit_priv = 0
		self.SK_Faktor_priv = 1
		self.SK_Offset_priv = 0
		self.ws = None

		self.thread = threading._DummyThread

		self.private_unit_s = 1
		logging.basicConfig()
		self.buffer = []
		self.list_SK = []
		self.list_SK_unit = []
		self.sortCol = 0

		self.conf = conf.Conf()
		self.home = self.conf.home
		self.currentpath = self.conf.get('GENERAL', 'op_folder')
		SK_ = SK_settings(self.conf)
		self.ws_name = SK_.ws+SK_.ip+":"+str(SK_.aktport)+"/signalk/v1/stream?subscribe=self"

		self.currentdir = '/home/pi/openplotter-SKfilter/openplotterSKfilter'
		self.currentLanguage = self.conf.get('GENERAL', 'lang')
		self.language = language.Language(self.currentdir,'openplotter-SKfilter',self.currentLanguage)
		#Language(self.conf)

		wx.Frame.__init__(self, None, title='diagnostic Signal K input', size=(770, 435))
		self.Bind(wx.EVT_CLOSE, self.OnClose)
		panel = wx.Panel(self, wx.ID_ANY)
		panel.SetBackgroundColour(wx.Colour(230,230,230,255))

		self.ttimer = 100
		self.timer = wx.Timer(self)
		self.Bind(wx.EVT_TIMER, self.timer_act, self.timer)

		self.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))

		icon = wx.Icon(self.currentdir+"/data/openplotter-24.png", wx.BITMAP_TYPE_PNG)
		self.SetIcon(icon)

		self.list = wx.ListCtrl(panel, -1, style=wx.LC_REPORT | wx.SUNKEN_BORDER)
		self.list.InsertColumn(0, _('SRC'), width=200)
		self.list.InsertColumn(1, _('Signal K'), width=310)
		self.list.InsertColumn(2, _('Value'), wx.LIST_FORMAT_RIGHT, width=190)
		self.list.InsertColumn(3, _('Unit'), width=45)
		self.list.InsertColumn(4, _('Interval'), wx.LIST_FORMAT_RIGHT, width=55)
		self.list.InsertColumn(5, _('Status'), width=50)
		self.list.InsertColumn(6, _('Description'), width=500)
		self.list.InsertColumn(7, _('label'), width=100)
		self.list.InsertColumn(8, _('type'), width=90)
		self.list.InsertColumn(9, _('pgn'), width=70)
		self.list.InsertColumn(10, _('src'), width=50)
		self.list.InsertColumn(11, _('sentence'), width=50)
		self.list.InsertColumn(12, _('talker'), width=50)

		sort_SRC = wx.Button(panel, label=_('Sort SRC'))
		sort_SRC.Bind(wx.EVT_BUTTON, self.on_sort_SRC)

		sort_SK = wx.Button(panel, label=_('Sort SK'))
		sort_SK.Bind(wx.EVT_BUTTON, self.on_sort_SK)

		show_keys = wx.Button(panel, label=_('Show All SK keys'))
		show_keys.Bind(wx.EVT_BUTTON, self.on_show_keys)

		self.private_unit = wx.CheckBox(panel, label=_('private Unit'), pos=(360, 32))
		self.private_unit.Bind(wx.EVT_CHECKBOX, self.on_private_unit)
		self.private_unit.SetValue(self.private_unit_s)

		unit_setting = wx.Button(panel, label=_('Unit Setting'))
		unit_setting.Bind(wx.EVT_BUTTON, self.on_unit_setting)

		vbox = wx.BoxSizer(wx.VERTICAL)
		hlistbox = wx.BoxSizer(wx.HORIZONTAL)
		hbox = wx.BoxSizer(wx.HORIZONTAL)
		hlistbox.Add(self.list, 1, wx.ALL | wx.EXPAND, 5)
		hbox.Add(sort_SRC, 0, wx.RIGHT | wx.LEFT, 5)
		hbox.Add(sort_SK, 0, wx.RIGHT | wx.LEFT, 5)
		hbox.Add(show_keys, 0, wx.RIGHT | wx.LEFT, 5)
		hbox.Add((0,0), 1, wx.RIGHT | wx.LEFT, 5)
		hbox.Add(self.private_unit, 0, wx.RIGHT | wx.LEFT, 5)
		hbox.Add(unit_setting, 0, wx.RIGHT | wx.LEFT, 5)
		vbox.Add(hlistbox, 1, wx.ALL | wx.EXPAND, 0)
		vbox.Add(hbox, 0, wx.ALL | wx.EXPAND, 0)
		panel.SetSizer(vbox)

		self.CreateStatusBar()

		self.read()
		self.start()

		self.Show(True)

		self.status = ''
		self.data = []
		self.baudc = 0
		self.baud = 0

		self.timer.Start(self.ttimer)
		self.no_action = 0
		self.no_action_limit = 5000 / self.ttimer

	def timer_act(self, e):
		if len(self.buffer) > 0:
			self.no_action = 0
			for ii in self.buffer:
				if 0 <= ii[0] < self.list.GetItemCount():
					self.list.SetItem(ii[0], ii[1], ii[2])
				else:
					self.sorting()
			self.buffer = []
		else:
			self.no_action += 1
			if self.no_action > self.no_action_limit:
				if self.ws:
					self.ws.close()
				self.start()
				self.no_action = 0

	def json_interval(self, time_old, time_new):
		sek_n = float(time_new[17:22])
		sek_o = float(time_old[17:22])
		if sek_n >= sek_o:
			dif = sek_n - sek_o
		else:
			dif = sek_n + 60 - sek_o
		return dif

	def read(self):
		self.list_SK_unit = []

		self.keys = GetKeys()
		data = self.keys.keys

		data_sk_unit_private = []
		if os.path.isfile(self.home+'/.openplotter/private_unit.json'):
			with open(self.home+'/.openplotter/private_unit.json') as data_file:
				data_sk_unit_private = ujson.load(data_file)

		for i in data:
			self.list_SK_unit.append([str(i[0]), str(i[2]), '', str(i[1])])
		for j in data_sk_unit_private:
			for i in self.list_SK_unit:
				if j[0] == i[0]:
					i[2] = j[2]
					break

		self.list_SK_unit.sort(key=lambda tup: tup[0])
		self.list_SK_unit.sort(key=lambda tup: tup[1])

		self.data_sk_star3 = []
		self.data_sk_star4 = []
		self.data_sk_1 = []
		self.data_sk_2 = []
		self.data_sk_3 = []
		self.data_sk_4 = []
		self.data_sk_5 = []
		for i in self.list_SK_unit:
			j=i[0].split('.')
			if "*" in i[0]:
				if len(j)==3:
					self.data_sk_star3.append(i)
				elif len(j)==4:
					self.data_sk_star4.append(i)
			else:
				if len(j)==3:
					self.data_sk_3.append(i)
				elif len(j)==4:
					self.data_sk_4.append(i)
				elif len(j)==1:
					self.data_sk_1.append(i)
				elif len(j)==2:
					self.data_sk_2.append(i)
				elif len(j)==5:
					self.data_sk_5.append(i)

	def lookup_star(self, name):
		j=name.split('.')
		erg=[]
		if len(j)==3:
			for i in self.data_sk_3:
				if name==i[0]:
					erg=i
					break
		elif len(j)==4:
			for i in self.data_sk_4:
				if name==i[0]:
					erg=i
					break
		elif len(j)==1:
			for i in self.data_sk_1:
				if name==i[0]:
					erg=i
					break
		elif len(j)==2:
			for i in self.data_sk_2:
				if name==i[0]:
					erg=i
					break
		elif len(j)==5:
			for i in self.data_sk_5:
				if name==i[0]:
					erg=i
					break

		if erg == []:
			if len(j)==3:
				for i in self.data_sk_star3:
					if (j[0]+".*."+j[2])==i[0]:
						erg=i
						break
					elif (j[0]+'.'+j[1]+'.*')==i[0]:
						erg=i
						break
			if len(j)==4:
				for i in self.data_sk_star4:
					if (j[0]+'.*.'+j[2]+'.'+j[3])==i[0]:
						erg=i
						break
					elif (j[0]+'.'+j[1]+'.*.'+j[3])==i[0]:
						erg=i
						break


		self.SK_unit = ''
		self.SK_unit_priv = ''
		self.SK_description = ''
		if erg != []:
			self.SK_unit = erg[1]
			self.SK_description = erg[3]
			if erg[2] != '':
				self.SK_unit_priv = erg[2]
			else:
				self.SK_unit_priv = erg[1]
		else:
			print(('no unit for ', name))

		self.SK_Faktor_priv = 1
		self.SK_Offset_priv = 0
		if self.SK_unit_priv != self.SK_unit:
			if self.SK_unit == 'Hz':
				if self.SK_unit_priv == 'RPM':
					self.SK_Faktor_priv = 0.0166666666
			elif self.SK_unit == 'K':
				if self.SK_unit_priv == 'C':
					self.SK_Offset_priv = -273.15
				elif self.SK_unit_priv == 'F':
					self.SK_Faktor_priv = 1.8
					self.SK_Offset_priv = -459.67
			elif self.SK_unit == 'J':
				if self.SK_unit_priv == 'Ah(12V)':
					self.SK_Faktor_priv = 43200.
				if self.SK_unit_priv == 'Ah(24V)':
					self.SK_Faktor_priv = 86400
			elif self.SK_unit == 'm':
				if self.SK_unit_priv == 'ft':
					self.SK_Faktor_priv = 0.3048
				elif self.SK_unit_priv == 'nm':
					self.SK_Faktor_priv = 1852
				elif self.SK_unit_priv == 'km':
					self.SK_Faktor_priv = 1000
			elif self.SK_unit == 'm/s':
				if self.SK_unit_priv == 'kn':
					self.SK_Faktor_priv = 0.514444444
				elif self.SK_unit_priv == 'kmh':
					self.SK_Faktor_priv = 0, 277778
				elif self.SK_unit_priv == 'mph':
					self.SK_Faktor_priv = 0.44704
			elif self.SK_unit == 'm3':
				if self.SK_unit_priv == 'dm3':
					self.SK_Faktor_priv = 0.001
				elif self.SK_unit_priv == 'gal':
					self.SK_Faktor_priv = 0.00378541
			elif self.SK_unit == 'm3/s':
				if self.SK_unit_priv == 'l/h':
					self.SK_Faktor_priv = 2.777778E-7
				elif self.SK_unit_priv == 'gal/h':
					self.SK_Faktor_priv = 0.0000010515
			elif self.SK_unit == 'Pa':
				if self.SK_unit_priv == 'hPa':
					self.SK_Faktor_priv = 100
				elif self.SK_unit_priv == 'Bar':
					self.SK_Faktor_priv = 100000
			elif self.SK_unit == 'rad' and self.SK_unit_priv == 'deg':
				self.SK_Faktor_priv = 0.0174533
			elif self.SK_unit == 's':
				if self.SK_unit_priv == 'h':
					self.SK_Faktor_priv = 3600
				elif self.SK_unit_priv == 'd':
					self.SK_Faktor_priv = 86400
				elif self.SK_unit_priv == 'y':
					self.SK_Faktor_priv = 31536000
			elif self.SK_unit == 'ratio':
				if self.SK_unit_priv == '%':
					self.SK_Faktor_priv = 0.01
		else:
			self.SK_Faktor_priv = 1
			self.SK_Offset_priv = 0

	def on_sort_SRC(self, e):
		self.sortCol = 0
		self.sorting()

	def on_sort_SK(self, e):
		self.sortCol = 1
		self.sorting()

	def on_show_keys(self,e):
		dlg = showKeys()
		res = dlg.ShowModal()
		dlg.Destroy()

	def sorting(self):
		self.list.DeleteAllItems()
		list_new = []
		for i in sorted(self.list_SK, key=lambda item: (item[self.sortCol])):
			list_new.append(i)
		self.list_SK = list_new
		self.init2()

	def init2(self):
		index = 0
		for i in self.list_SK:
			if type(i[2]) is float:
				pass
			elif type(i[2]) is str:
				pass
			else:
				i[2] = 0.0
			self.list.InsertItem(index, str(i[0]))
			self.list.SetItem(index, 1, str(i[1]))

			if not self.private_unit_s:
				if type(i[2]) is str:
					self.buffer.append([index, 2, i[2]])
				else:
					self.buffer.append([index, 2, str('%.3f' % i[2])])
				self.buffer.append([index, 3, i[3]])
			else:
				if type(i[2]) is str:
					self.buffer.append([index, 2, i[2]])
				else:
					i[9] = i[2] / i[10] + i[11]
					self.buffer.append([index, 2, str('%.3f' % i[9])])
				self.buffer.append([index, 3, i[8]])
			self.list.SetItem(index, 4, str('%.1f' % i[4]))
			self.list.SetItem(index, 5, str(i[5]))
			self.list.SetItem(index, 6, str(i[6]))
			self.list.SetItem(index, 7, str(i[12]))
			self.list.SetItem(index, 8, str(i[13]))
			self.list.SetItem(index, 9, str(i[14]))
			self.list.SetItem(index,10, str(i[15]))
			self.list.SetItem(index,11, str(i[16]))
			self.list.SetItem(index,12, str(i[17]))
			index += 1

	def on_unit_setting(self, e):
		subprocess.Popen(['python3', self.currentdir + '/unit-private.py'])

	def OnClose(self, e):
		self.endlive=True

		if self.ws:
			self.ws.close()
		self.timer.Stop()
		self.Destroy()

	def on_message(self, ws, message):
		type = ''
		talker = ''
		sentence = ''
		src_ = ''
		pgn = ''
		label = ''
		src = ''
		type = ''
		value = ''


		if self.endlive:
			self.on_close(ws)
			self.ende=True
			return
			js_upb=''
		#if True:
		try:
			js_upb = ujson.loads(message)
			if 'updates' not in js_upb:
				return
			js_up = js_upb['updates'][0]

			if 'source' in list(js_up.keys()):
				source=js_up['source']
				label = source['label']
				if 'type' in source:
					type = source['type']
					if type == 'NMEA0183':
						if 'talker' in source:
							talker = source['talker']
							src =label+'.'+talker
							if 'sentence' in source:
								sentence = source['sentence']
								src =label+'.'+sentence
					elif type == 'NMEA2000':
						if 'src' in source:
							src_ = source['src']
							src =label+'.'+src_
							if 'pgn' in source:
								pgn = source['pgn']
								src +='.'+str(pgn)
			if '$source' in js_up and src=='':
				src = js_up['$source']
			if 'timestamp' in list(js_up.keys()):
				timestamp = js_up['timestamp']
			else:
				timestamp = '2000-01-01T00:00:00.000Z'
			values_ = js_up['values']
			for values in values_:
				path = values['path']
				value = values['value']
				src2 = src
				timestamp2 = timestamp
				if isinstance(value, dict):
					if 'timestamp' in value: timestamp2 = value['timestamp']
					if '$source' in value and src=='':
						src = value['$source']
					elif 'source' in value:
						source=value['source']
						label = source['label']
						if 'type' in source:
							type = source['type']
							if type == 'NMEA0183':
								if 'talker' in source:
									talker = source['talker']
									src =label+'.'+talker
									if 'sentence' in source:
										sentence = source['sentence']
										src =label+'.'+sentence
							elif type == 'NMEA2000':
								if 'src' in source:
									src_ = source['src']
									src =label+'.'+src_
									if 'pgn' in source:
										pgn = source['pgn']
										src +='.'+str(pgn)
					for lvalue in value:
						result = True
						if lvalue in ['source', '$source', 'method']:
							result = False
						elif lvalue == 'timestamp':
							if 'position' in path and 'RMC' in src2:
								self.update_add(timestamp2, 'navigation.datetime', src2, timestamp2,label,type,pgn,src_,sentence,talker)
							result = False
						if result:
							path2 = path + '.' + lvalue
							value2 = value[lvalue]
							self.update_add(value2, path2, src2, timestamp2,label,type,pgn,src_,sentence,talker)

				else:
					self.update_add(value, path, src, timestamp,label,type,pgn,src_,sentence,talker)


		except:
			print('Error when parsing this sentence:')
			print(js_upb)


	def update_add(self, value, path, src, timestamp,label,type,pgn,src_,sentence,talker):
		# SRC SignalK Value Unit Interval Status Description timestamp  private_Unit private_Value priv_Faktor priv_Offset label type pgn src_ sentence talker
		#  0    1      2     3      4        5        6          7           8             9           10          11       12    13   14  15     16      17
		if isinstance(value, list): value = value[0]
		#if type(value) is list: value = value[0]

		if isinstance(value, float): pass
		elif isinstance(value, str): value = str(value)
		elif isinstance(value, int): value = float(value)
		elif value is None: value = 'None'
		else: value=0.0

		index = 0
		exists = False
		for i in self.list_SK:
			if path == i[1] and i[0] == src:
				exists = True
				i[0] = src
				i[2] = value
				if i[4] == 0.0:
					i[4] = self.json_interval(i[7], timestamp)
				else:
					i[4] = i[4] * .6 + 0.4 * self.json_interval(i[7], timestamp)
				i[7] = timestamp
				self.buffer.append([index, 0, i[0]])
				self.buffer.append([index, 4, str('%.2f' % i[4])])
				if isinstance(i[2], str):
				#if type(i[2]) is str:
					self.buffer.append([index, 2, i[2]])
					self.buffer.append([index, 3, i[3]])
					break
				elif isinstance(i[2], float):
				#elif type(i[2]) is float:
					pass
				else:
					i[2] = 0.0
				if not self.private_unit_s:
					self.buffer.append([index, 2, str('%.3f' % i[2])])
					self.buffer.append([index, 3, i[3]])
				else:
					i[9] = i[2] / i[10] + i[11]
					self.buffer.append([index, 2, str('%.3f' % i[9])])
					self.buffer.append([index, 3, i[8]])
				break
			index += 1
		if not exists:
			self.lookup_star(path)
			self.list_SK.append(
				[src, path, value, str(self.SK_unit), 0.0, 1, self.SK_description, timestamp, str(self.SK_unit_priv), 0,
				 self.SK_Faktor_priv, self.SK_Offset_priv,label,type,str(pgn),src_,sentence,talker])
			self.buffer.append([-1, 0, ''])

	def on_private_unit(self, e):
		self.private_unit_s = self.private_unit.GetValue()

	def on_error(self, ws, error):
		print(error)

	def on_close(self, ws):
		ws.close()

	def on_open(self, ws):
		pass

	def run(self):
		self.endlive=False
		self.ende=False
		self.ws = websocket.WebSocketApp(self.ws_name,
										 on_message=lambda ws, msg: self.on_message(ws, msg),
										 on_error=lambda ws, err: self.on_error(ws, err),
										 on_close=lambda ws: self.on_close(ws))
		self.ws.on_open = lambda ws: self.on_open(ws)
		self.ws.run_forever()
		self.ws = None

	def start(self):
		def run():
			self.run()

		self.thread = threading.Thread(target=run)
		self.thread.start()

################################################################################

class SK_settings:

	def __init__(self, conf):
		self.installed = False
		self.conf = conf
		self.home = os.path.expanduser("~")
		self.setting_file = self.home+'/.signalk/settings.json'
		self.load()

	def load(self):
		if os.path.exists(self.setting_file):
			with open(self.setting_file) as data_file:
				self.data = ujson.load(data_file)
			self.installed = True			
		else:
			self.data = {}

		self.sslport = -1
		if 'sslport' in self.data: self.sslport = self.data['sslport']
		self.port = -1
		if 'port' in self.data: self.port = self.data['port']
		self.ssl = -1
		if 'ssl' in self.data: self.ssl = self.data['ssl']
		if (self.ssl == -1 or self.ssl == False) and self.port == -1: self.port = 3000
		self.http = 'http://'
		self.ws = 'ws://'
		self.aktport = self.port
		if self.ssl:
			self.http = 'https://'
			self.ws = 'wss://'
			self.aktport = self.sslport
		self.ip = 'localhost'
		self.http_address = self.http+self.ip+':'+str(self.aktport)


	def setSKsettings(self):
		write = False
		serialInst = self.conf.get('UDEV', 'Serialinst')
		try: serialInst = eval(serialInst)
		except: serialInst = {}
		#serial NMEA 0183 devices
		for alias in serialInst:
			if serialInst[alias]['data'] == 'NMEA 0183' and serialInst[alias]['assignment'] == 'Signal K > OpenCPN':
				exists = False
				if 'pipedProviders' in self.data:
					count = 0
					for i in self.data['pipedProviders']:
						if i['id'] == alias:
							exists = True
							if i['pipeElements'][0]['options']['subOptions']['baudrate'] != int(serialInst[alias]['bauds']):
								write = True
								self.data['pipedProviders'][count]['pipeElements'][0]['options']['subOptions']['baudrate'] = int(serialInst[alias]['bauds'])
						count = count + 1
				if not exists:
					self.data['pipedProviders'].append({'pipeElements': [{'type': 'providers/simple', 'options': {'logging': False, 'type': 'NMEA0183', 'subOptions': {"validateChecksum": True, "type": "serial", "device": '/dev/'+alias, "baudrate": int(serialInst[alias]['bauds'])}}}], 'enabled': True, 'id': alias})
					write = True
		count = 0
		for i in self.data['pipedProviders']:
			if 'ttyOP_' in i['id'] and i['pipeElements'][0]['options']['subOptions']['type'] == 'serial':
				exists = False
				for alias in serialInst:
					if alias == i['id'] and serialInst[alias]['data'] == 'NMEA 0183' and serialInst[alias]['assignment'] == 'Signal K > OpenCPN':
						exists = True
				if not exists:
					write = True
					del self.data['pipedProviders'][count]
			count = count + 1
		#serial NMEA 2000 devices
		for alias in serialInst:
			if serialInst[alias]['data'] == 'NMEA 2000' and serialInst[alias]['assignment'] == 'Signal K > OpenCPN':
				exists = False
				if 'pipedProviders' in self.data:
					count = 0
					for i in self.data['pipedProviders']:
						if i['id'] == alias:
							exists = True
							if i['pipeElements'][0]['options']['subOptions']['baudrate'] != int(serialInst[alias]['bauds']):
								write = True
								self.data['pipedProviders'][count]['pipeElements'][0]['options']['subOptions']['baudrate'] = int(serialInst[alias]['bauds'])
						count = count + 1
				if not exists:
					self.data['pipedProviders'].append({'pipeElements': [{'type': 'providers/simple', 'options': {'logging': False, 'type': 'NMEA2000', 'subOptions': {'device': '/dev/'+alias, "baudrate": int(serialInst[alias]['bauds']), 'type': 'ngt-1-canboatjs'}}}], 'enabled': True, 'id': alias})
					write = True
		count = 0
		for i in self.data['pipedProviders']:
			if 'ttyOP_' in i['id'] and i['pipeElements'][0]['options']['subOptions']['type'] == 'ngt-1-canboatjs':
				exists = False
				for alias in serialInst:
					if alias == i['id'] and serialInst[alias]['data'] == 'NMEA 2000' and serialInst[alias]['assignment'] == 'Signal K > OpenCPN':
						exists = True
				if not exists:
					write = True
					del self.data['pipedProviders'][count]
			count = count + 1

		if write: self.write_settings()
		return write

	def write_settings(self):
		data = ujson.dumps(self.data, indent=4, sort_keys=True)
		try:
			wififile = open(self.setting_file, 'w')
			wififile.write(data.replace('\/','/'))
			wififile.close()
			self.load()
		except: print('Error: error saving Signal K settings')

################################################################################

app = wx.App()
MyFrame().Show()
app.MainLoop()
