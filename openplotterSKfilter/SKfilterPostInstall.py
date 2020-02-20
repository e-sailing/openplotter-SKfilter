#!/usr/bin/env python3

# This file is part of Openplotter.
# Copyright (C) 2019 by e-sailing <https://github.com/openplotter/openplotter-SKfilter>
#
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

import os, subprocess
from openplotterSettings import conf
from openplotterSettings import language
from openplotterSettings import platform
from .version import version

def main():
	conf2 = conf.Conf()
	currentdir = os.path.dirname(os.path.abspath(__file__))
	currentLanguage = conf2.get('GENERAL', 'lang')
	language.Language(currentdir,'openplotter-SKfilter',currentLanguage)
	platform2 = platform.Platform()
	
	try:
		print(_('Installing/Updating Node-Red (Signal K embedded)...'))
		if platform2.skDir:
			subprocess.call(['npm', 'i', '--verbose', '@signalk/signalk-node-red'], cwd = platform2.skDir)
			subprocess.call(['chown', '-R', conf2.user, platform2.skDir])
			subprocess.call(['systemctl', 'stop', 'signalk.service'])
			subprocess.call(['systemctl', 'stop', 'signalk.socket'])
			subprocess.call(['systemctl', 'start', 'signalk.socket'])
			subprocess.call(['systemctl', 'start', 'signalk.service'])
		else: 
			print(_('Failed. Please, install Signal K server'))
		print(_('DONE'))
	except Exception as e: print(_('FAILED: ')+str(e))

	print(_('Setting version...'))
	try:
		conf2.set('APPS', 'SKfilter', version)
		print(_('DONE'))
	except Exception as e: print(_('FAILED: ')+str(e))

if __name__ == '__main__':
	main()
