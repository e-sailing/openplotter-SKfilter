# OpenPlotter Signal K Filter
Some devices have wrong data or data that conflicts with other devices.

This app filters unwanted Signal K sentences.

Requirement

             openplotter-settings ,
             @signalk/signalk-node-red

## Build this package as a deb file
Install requirements

    $ sudo apt-get install fakeroot python3-all
    $ sudo pip3 install stdeb3
    $ sudo apt-get install devscripts

Clone and build
    
    $ git clone https://github.com/e-sailing/openplotter-SKfilter.git
    $ cd openplotter-SKfilter
    $ python3 setup.py --command-packages=stdeb3.command bdist_deb

Install

The installation of the created deb file (~/openplotter-SKfilter/deb_dist/python3-openplotterskfilter_2.x-x_all.deb)
can be started from the file manager.

Run

You can start OpenPlotter Signal K Filter from the menu->other.

Or with

    $ openplotter-SKfilter

To uninstall the package

    $ sudo apt-get purge python3-openplotterskfilter

## Standard installation

Clone and install

    $ git clone https://github.com/e-sailing/openplotter-SKfilter.git
    $ cd openplotter-SKfilter
    $ sudo python3 setup.py install

Run

    $ openplotter-SKfilter
