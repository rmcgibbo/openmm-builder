openmm-builder
==============

A graphical interface for building OpenMM scripts. As you edit the fields in the GUI, the script will
update itself in real time.

![image](https://raw.github.com/rmcgibbo/openmm-builder/master/screenshot.png)

Dependencies
------------
openmm-builder is a GUI app. Currently, it runs using the Qt graphics toolkit, although that should be
flexible. If you don't know what any of this this means, and are using a vendor-provided python
distribution, YOUR SYSTEM PYTHON MIGHT NOT BE LINKED AGAINST A GRAPHICS TOOLKIT. So, we HIGHLY
RECOMMEND that you download a "full featured" python distribution like EPD Free, which you can get
here: http://www.enthought.com/products/epd_free.php

openmm-builder depends on enthought's [traits](https://pypi.python.org/pypi/traits) and
[traitsui](https://pypi.python.org/pypi/traitsui). Obviously if you're using the EPD python
distribution (recommended), you will already have these packages. If not, you can install them
with

```
$ sudo easy_install traits traitsui
```
 
We are also, for simplicity, using [mustache](http://mustache.github.com/) to generate the script. To
install this package into your python distribution with `easy_install`, just run:

```
$ sudo easy_install pystache
```

BOOM!

Installation
------------
Just run

```
sudo python setup.py install
```

Now the script `openmm-builder` will be installed in your PATH!
