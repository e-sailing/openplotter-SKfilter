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

from setuptools import setup
from openplotterSKfilter import version

setup (
	name = 'openplotterSKfilter',
	version = version.version,
	description = 'This is a template to help create apps for OpenPlotter',
	license = 'GPLv3',
	author="e-sailing",
	author_email='e.minus.sailing@gmail.com',
	url='https://github.com/openplotter/openplotter-SKfilter',
	packages=['openplotterSKfilter'],
	classifiers = ['Natural Language :: English',
	'Operating System :: POSIX :: Linux',
	'Programming Language :: Python :: 3'],
	include_package_data=True,
	#entry_points={'console_scripts': ['openplotter-SKfilter=openplotterSKfilter.openplotterSKfilter:main'],'console_scripts2': ['openplotter-diagnostic-SK=openplotterSKfilter.diagnostic-SK-input:main'],},
	entry_points={'console_scripts': ['openplotter-SKfilter=openplotterSKfilter.openplotterSKfilter:main'],},
	data_files=[('share/applications', ['openplotterSKfilter/data/openplotter-SKfilter.desktop']),('share/pixmaps', ['openplotterSKfilter/data/openplotter-SKfilter.png']),('share/applications', ['openplotterSKfilter/data/openplotter-diagnostic-SK.desktop']),],
	)
