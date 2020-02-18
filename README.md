# OpenPlotter Signal K Filter
Some devices have wrong data or data that conflicts with other devices.

This app filters unwanted Signal K sentences.

### Installing

#### For production

Install [openplotter-settings](https://github.com/openplotter/openplotter-settings) for **production** and install Dashboard. In Dashboard install nodered.
Then install this app from *OpenPlotter Apps* tab.

#### For development

Install [openplotter-settings](https://github.com/openplotter/openplotter-settings) for **production** and install Dashboard. In Dashboard install nodered.

Install dependencies:

`sudo apt install python3-websocket`

Clone the repository:

`git clone https://github.com/openplotter/openplotter-SKfilter`

Make your changes and create the package:

```
cd openplotter-SKfilter
dpkg-buildpackage -b
```

Install the package:

```
cd ..
sudo dpkg -i openplotter-SKfilter_x.x.x-xxx_all.deb
```

Run post-installation script:

`sudo SKfilterPostInstall`

Run:

`openplotter-SKfilter`

Make your changes and repeat package, installation and post-installation steps to test. Pull request your changes to github and we will check and add them to the next version of the [Debian package](https://cloudsmith.io/~openplotter/repos/openplotter/packages/).

### Documentation

https://openplotter.readthedocs.io

### Support

http://forum.openmarine.net/forumdisplay.php?fid=1