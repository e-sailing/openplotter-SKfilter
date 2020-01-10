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

import ujson, wx, os, subprocess, sys
from openplotterSettings import conf

class GetKeys:
	def __init__(self):
		keys = []

		conf_ = conf.Conf()
		sk_folder = conf_.get('GENERAL', 'sk_folder')
		self.data = ""

		node_path_all = subprocess.check_output(['npm', 'config', 'get', 'prefix']).decode(sys.stdin.encoding)
		node_path_line = node_path_all.split('\n')
		node_path = '/usr'
		print(node_path_line)
		if len(node_path_line) > 0:
			node_path = node_path_line[len(node_path_line) - 1]
			print(node_path_line[len(node_path_line) - 1])
			if len(node_path_line) > 1 and node_path == '':
				node_path = node_path_line[len(node_path_line) - 2]
				print(node_path_line[len(node_path_line) - 2])
		keyswithmetadata = node_path+'/lib/node_modules/signalk-server/node_modules/@signalk/signalk-schema/dist/keyswithmetadata.json'

		try:
			with open(keyswithmetadata) as data_file:
				self.data = ujson.load(data_file)
		except: self.ShowMessage(_('File not found: ')+keyswithmetadata)

		for i in self.data:
			if '/vessels/*/' in i:
				key = i.replace('/vessels/*/','')
				key = key.replace('RegExp','*')
				key = key.replace('[A-Za-z0-9]+','*')
				key = key.replace('/','.')
				if 'properties' in self.data[i]:
					for ii in self.data[i]['properties']:
						key2 = key+'.'+ii
						if 'description' in self.data[i]['properties'][ii]: description = self.data[i]['properties'][ii]['description']
						else: description = '[missing]'
						if 'units' in self.data[i]['properties'][ii]: units = self.data[i]['properties'][ii]['units']
						else: units = ''
						keys.append([str(key2),description,units])
				else:
					if 'description' in self.data[i]: description = self.data[i]['description']
					else: description = '[missing]'
					if 'units' in self.data[i]: units = self.data[i]['units']
					else: units = ''
					keys.append([str(key),description,units])
		list_tmp = []
		groups = [_('ungrouped')]
		ungrouped = []
		for i in keys:
			items=i[0].split('.')
			if not items[0] in list_tmp:
				list_tmp.append(items[0])
			else:
				if not items[0] in groups:
					groups.append(items[0])
		for i in list_tmp:
			if not i in groups: ungrouped.append(i)

		self.keys = sorted(keys)
		self.groups = sorted(groups)
		self.ungrouped = sorted(ungrouped)

	def ShowMessage(self, w_msg):
		wx.MessageBox(w_msg, 'Info', wx.OK | wx.ICON_INFORMATION)
